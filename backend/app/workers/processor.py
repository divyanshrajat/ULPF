import asyncio
import logging
import uuid
from datetime import datetime

from app.core.queue import event_queue
from app.core.database import SessionLocal
from app.services.rules.fingerprint import generate_fingerprint
from app.services.rules.registry import find_active_rule_by_fingerprint
from app.services.rules.parsers.factory import ParserFactory, ParserError
from app.services.normalization.engine import normalization_engine
from app.models.domain import (
    DeadLetter, RawIndex, UnresolvedEvent, NormalizedEvent, Trace
)
from app.core.config import settings

logger = logging.getLogger(__name__)

def _create_dead_letter(db, trace_id, source_id, stage, error):
    try:
        raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
        raw_ref = raw_idx.storage_uri if raw_idx else f"vault://{source_id}/unknown/{trace_id}.raw"
        existing = db.query(DeadLetter).filter(DeadLetter.trace_id == trace_id).first()
        if not existing:
            dl = DeadLetter(
                trace_id=trace_id,
                source_id=source_id,
                stage=stage,
                error_class=error.__class__.__name__,
                diagnostic=str(error)[:500],
                raw_reference=raw_ref,
                created_at=datetime.utcnow(),
            )
            db.add(dl)
            db.commit()
    except Exception as inner_e:
        logger.error(f"Failed to create dead letter for {trace_id}: {inner_e}")

async def process_event(record):
    db = SessionLocal()
    trace_id = record.trace_id
    source_id = record.source_id
    
    try:
        # decode payload if it's bytes
        if isinstance(record.payload, bytes):
            raw_event = record.payload.decode('utf-8', errors='replace')
        else:
            raw_event = record.payload

        # S2: Fingerprint
        fingerprint = generate_fingerprint(raw_event)
        
        # S3: Active Rule Registry Lookup
        active_rule_version = find_active_rule_by_fingerprint(db, fingerprint)
        
        if active_rule_version:
            # FAST PATH
            try:
                parser = ParserFactory.create(
                    active_rule_version.parser_type, 
                    active_rule_version.parser_definition, 
                    active_rule_version.field_mappings
                )
                
                parsed_data = parser.parse(raw_event)
                
                # Check required fields
                if active_rule_version.required_fields:
                    for req in active_rule_version.required_fields:
                        if req not in parsed_data:
                            raise Exception(f"Missing required field: {req}")

                # S6: Normalization
                raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
                digest = raw_idx.digest if raw_idx else "sha256:unknown"

                raw_ref = {
                    "trace_id": trace_id,
                    "digest": digest,
                    "byte_length": record.byte_length,
                }
                
                # We reuse the existing normalization_engine but with our deterministic data
                normalized_event, _ = normalization_engine.normalize(
                    db=db,
                    parsed_data=parsed_data,
                    source_id=source_id,
                    template_id=None,
                    trace_id=trace_id,
                    raw_ref=raw_ref,
                    detection=None,
                )

                # Persist NormalizedEvent
                ne = NormalizedEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    source_id=source_id,
                    schema_version=active_rule_version.schema_version,
                    rule_id=active_rule_version.rule_id,
                    rule_version=active_rule_version.version,
                    processing_path="fast_path",
                    normalized_payload=normalized_event.dict(),
                    created_at=datetime.utcnow(),
                )
                db.add(ne)
                
                # Update Trace
                trace = db.query(Trace).filter(Trace.trace_id == trace_id).first()
                if trace:
                    trace.rule_id = active_rule_version.rule_id
                    trace.rule_version = active_rule_version.version
                    trace.rule_hash = active_rule_version.rule_hash
                    trace.schema_version = active_rule_version.schema_version
                    
                db.commit()
                
                logger.info(f"[FAST PATH COMPLETE] trace_id={trace_id} rule={active_rule_version.rule_id} v{active_rule_version.version}")

                # (Optional MVP: Delivery to OpenSearch could happen here)
                try:
                    from app.core.time import to_ist_iso
                    from app.core.opensearch import get_opensearch_client, index_event
                    os_client = get_opensearch_client()
                    event_dict = normalized_event.dict()
                    event_dict["trace_id"] = trace_id
                    event_dict["source_id"] = source_id
                    event_dict["processing_path"] = "fast_path"
                    event_dict["@timestamp"] = to_ist_iso()
                    index_event(os_client, event_dict)
                except Exception:
                    pass # non-fatal

            except ParserError as e:
                _create_dead_letter(db, trace_id, source_id, "parser_failed", e)
            except Exception as e:
                _create_dead_letter(db, trace_id, source_id, "validation_failed", e)
        else:
            # MISS -> UNRESOLVED -> Route to Onboarding
            unresolved = UnresolvedEvent(
                id=str(uuid.uuid4()),
                trace_id=trace_id,
                fingerprint=fingerprint,
            )
            db.add(unresolved)
            db.commit()
            logger.info(f"[UNRESOLVED] trace_id={trace_id} fingerprint={fingerprint[:20]}... routed to onboarding")
            
    except Exception as e:
        logger.error(f"Error processing trace {trace_id}: {e}")
        _create_dead_letter(db, trace_id, source_id, "unexpected_error", e)
    finally:
        db.close()
        event_queue.ack(record)

async def worker_loop():
    logger.info("ULPF processing worker started. Listening for ingestion events.")
    while True:
        try:
            record = await event_queue.consume()
            await process_event(record)
        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            await asyncio.sleep(1)
