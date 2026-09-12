import asyncio
import logging
from typing import Optional
from app.core.database import SessionLocal
from app.models.domain import UnresolvedEvent, RawIndex
from app.services.preservation.vault import vault
from app.core.queue import event_queue, EventRecord

logger = logging.getLogger(__name__)

async def republish_unresolved_events(rule_id: Optional[str] = None, fingerprint: Optional[str] = None):
    """
    Background task to automatically reprocess unresolved events when a rule is approved.
    It reads the raw payloads from the vault and pushes them back onto the main event queue
    so they go through the standard normalization pipeline again.
    """
    db = SessionLocal()
    try:
        query = db.query(UnresolvedEvent)
        if fingerprint:
            query = query.filter(UnresolvedEvent.fingerprint == fingerprint)
        
        # If we only have rule_id, we can't easily filter unresolved events directly by rule_id
        # because UnresolvedEvent only has fingerprint. We would need to join with RuleFingerprint.
        if rule_id and not fingerprint:
            from app.models.domain import RuleFingerprint
            fingerprints = db.query(RuleFingerprint).filter(RuleFingerprint.rule_id == rule_id).all()
            fp_list = [f.fingerprint for f in fingerprints]
            if fp_list:
                query = query.filter(UnresolvedEvent.fingerprint.in_(fp_list))
            else:
                logger.warning(f"No fingerprints found for rule {rule_id}, skipping reprocessing.")
                return
                
        unresolved_events = query.all()
        count = len(unresolved_events)
        if count == 0:
            logger.info("No unresolved events found to reprocess.")
            return
            
        logger.info(f"Reprocessing {count} unresolved events...")
        republished = 0
        failed = 0
        
        for ev in unresolved_events:
            raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == ev.trace_id).first()
            if not raw_idx:
                failed += 1
                continue
                
            try:
                # Read from vault
                raw_bytes = await vault.read_event(raw_idx.source_id, raw_idx.received_at, raw_idx.trace_id)
                record = EventRecord(
                    trace_id=raw_idx.trace_id,
                    source_id=raw_idx.source_id,
                    payload=raw_bytes,
                    byte_length=raw_idx.byte_length
                )
                await event_queue.publish(record)
                
                # Delete the unresolved event record so it doesn't get processed again
                db.delete(ev)
                republished += 1
                
                # Commit in batches to avoid locking the DB for too long
                if republished % 100 == 0:
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to republish event {ev.trace_id}: {e}")
                failed += 1
                
        db.commit()
        logger.info(f"Finished reprocessing. Republished: {republished}, Failed: {failed}")
        
    finally:
        db.close()
