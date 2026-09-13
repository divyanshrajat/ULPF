import asyncio
import logging
import uuid
from datetime import datetime

from app.core.database import SessionLocal
from app.core.queue import event_queue
from app.models.domain import (
    DeadLetter,
    NormalizedEvent,
    RawIndex,
    Trace,
    UnresolvedEvent,
)
from app.services.normalization.engine import normalization_engine
from app.services.rules.fingerprint import generate_fingerprint
from app.services.rules.parsers.base import ParserError
from app.services.rules.parsers.factory import ParserFactory
from app.services.rules.registry import find_active_rule_by_fingerprint

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
        # Idempotency pre-check
        from app.models.domain import NormalizedEvent, UnresolvedEvent, DeadLetter
        if db.query(NormalizedEvent).filter(NormalizedEvent.trace_id == trace_id).first() or \
           db.query(UnresolvedEvent).filter(UnresolvedEvent.trace_id == trace_id).first() or \
           db.query(DeadLetter).filter(DeadLetter.trace_id == trace_id).first():
            logger.info(f"[IDEMPOTENCY] trace_id={trace_id} already processed, skipping.")
            return

        # decode payload if it's bytes
        if isinstance(record.payload, bytes):
            raw_event = record.payload.decode('utf-8', errors='replace')
        else:
            raw_event = record.payload

        fingerprint = None
        active_rule_version = None
        is_spot_check = False
        locked_rule_version_id = None
        
        # Check for active lock
        from app.models.domain import RuleLock, RuleVersion
        lock = None
        if getattr(record, 'session_id', None):
            lock = db.query(RuleLock).filter(RuleLock.session_id == record.session_id).first()
        elif getattr(record, 'job_id', None):
            lock = db.query(RuleLock).filter(RuleLock.job_id == record.job_id).first()
            
        if lock and lock.status == "LOCKED" and lock.rule_version_id:
            locked_rule_version_id = lock.rule_version_id
            
            spot_check_rate = 500
            if lock.mismatch_count > 0 and lock.events_since_mismatch < 50:
                spot_check_rate = 25
            elif lock.events_since_lock < 100:
                spot_check_rate = 50
                
            if (lock.events_since_lock + 1) % spot_check_rate == 0:
                is_spot_check = True
            else:
                active_rule_version = db.query(RuleVersion).filter(RuleVersion.id == lock.rule_version_id).first()
            
        if not active_rule_version:
            # S2: Fingerprint
            fingerprint = generate_fingerprint(raw_event, vendor_token=source_id)
            
            # S3: Active Rule Registry Lookup
            active_rule_version = find_active_rule_by_fingerprint(db, fingerprint)

            # S3b: Fallback Evaluation (Fingerprint Discovery)
            if not active_rule_version:
                from app.models.domain import Source, Rule, RuleVersion
                from app.services.rules.registry import add_fingerprint_to_rule
                
                source = db.query(Source).filter(Source.source_id == source_id).first()
                if source:
                    active_rules = db.query(Rule).filter(Rule.tenant_id == source.tenant_id, Rule.status == "ACTIVE").all()
                    for r in active_rules:
                        rv = db.query(RuleVersion).filter(RuleVersion.rule_id == r.rule_id, RuleVersion.status == "ACTIVE").first()
                        if rv:
                            try:
                                parser = ParserFactory.get_cached_parser(rv.id, rv.parser_type, rv.parser_definition, rv.field_mappings)
                                parsed = parser.parse(raw_event)
                                from app.services.rules.validator import RuleValidator
                                RuleValidator.validate_extracted_fields(parsed, rv.required_fields, rv.type_constraints)
                                
                                # Match found!
                                active_rule_version = rv
                                # Associate new fingerprint so future events take O(1) fast path
                                add_fingerprint_to_rule(db, r.rule_id, fingerprint)
                                logger.info(f"[DISCOVERY] Associated new fingerprint {fingerprint[:8]}... with rule {r.rule_id}")
                                break
                            except Exception:
                                continue
        
        if active_rule_version:
            # FAST PATH
            try:
                parser = ParserFactory.get_cached_parser(
                    active_rule_version.id,
                    active_rule_version.parser_type, 
                    active_rule_version.parser_definition, 
                    active_rule_version.field_mappings
                )
                
                parsed_data = await asyncio.to_thread(parser.parse, raw_event)
                
                from app.services.rules.validator import RuleValidator, ValidationError
                try:
                    await asyncio.to_thread(
                        RuleValidator.validate_extracted_fields,
                        parsed_data, 
                        active_rule_version.required_fields, 
                        active_rule_version.type_constraints
                    )
                except ValidationError as ve:
                    raise ParserError(f"Validation failed: {ve}")

                # S6: Normalization
                raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
                digest = raw_idx.digest if raw_idx else "sha256:unknown"

                raw_ref = {
                    "trace_id": trace_id,
                    "digest": digest,
                    "byte_length": record.byte_length,
                }
                
                # We reuse the existing normalization_engine but with our deterministic data
                normalized_event, provenance_records = normalization_engine.normalize(
                    db=db,
                    parsed_data=parsed_data,
                    source_id=source_id,
                    template_id=active_rule_version.id,
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
                    normalized_payload=normalized_event,
                    created_at=datetime.utcnow(),
                )
                db.add(ne)
                
                # Persist Provenance
                from app.models.domain import Provenance
                for pr in provenance_records:
                    p = Provenance(
                        trace_id=pr.trace_id,
                        target_field=pr.target_field,
                        source_field=pr.source_field,
                        source_value=pr.source_value,
                        transformation=pr.transformation,
                        mapping_id=pr.mapping_id,
                        mapping_version=pr.mapping_version,
                        schema_version=pr.schema_version,
                        confidence=pr.confidence,
                        decision=pr.decision,
                        created_at=datetime.utcnow()
                    )
                    db.add(p)
                
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
                    from app.core.opensearch import get_opensearch_client, index_event
                    from app.core.time import to_ist_iso
                    os_client = get_opensearch_client()
                    event_dict = normalized_event.copy()
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
                session_id=getattr(record, 'session_id', None),
                job_id=getattr(record, 'job_id', None)
            )
            db.add(unresolved)
            db.commit()
            logger.info(f"[UNRESOLVED] trace_id={trace_id} fingerprint={fingerprint[:20]}... routed to onboarding")
            
        # Update Session/Job counters atomically to prevent race conditions under high concurrency
        from sqlalchemy import update
        
        def update_container_counters(container_model, container_id, active_rule_version):
            if active_rule_version:
                db.execute(update(container_model).where(container_model.id == container_id).values(
                    processed_events=container_model.processed_events + 1,
                    normalized_count=container_model.normalized_count + 1
                ))
            else:
                db.execute(update(container_model).where(container_model.id == container_id).values(
                    processed_events=container_model.processed_events + 1,
                    unresolved_count=container_model.unresolved_count + 1
                ))

        if getattr(record, 'session_id', None):
            from app.models.domain import IngestionSession, RuleLock
            update_container_counters(IngestionSession, record.session_id, active_rule_version)
            lock = db.query(RuleLock).filter(RuleLock.session_id == record.session_id).first()
        elif getattr(record, 'job_id', None):
            from app.models.domain import IngestionJob, RuleLock
            update_container_counters(IngestionJob, record.job_id, active_rule_version)
            lock = db.query(RuleLock).filter(RuleLock.job_id == record.job_id).first()
        else:
            lock = None

        if lock:
            if lock.status == "SAMPLING":
                if active_rule_version:
                    db.execute(update(RuleLock).where(RuleLock.id == lock.id).values(
                        sample_count_seen=RuleLock.sample_count_seen + 1
                    ))
                    lock = db.query(RuleLock).filter(RuleLock.id == lock.id).first()
                    if lock.sample_count_seen >= 10:
                        db.execute(update(RuleLock).where(RuleLock.id == lock.id).values(
                            status="LOCKED",
                            rule_version_id=active_rule_version.id,
                            events_since_lock=0,
                            events_since_mismatch=0,
                            mismatch_count=0
                        ))
                else:
                    # Do not increment mismatch_count in SAMPLING; it is meant for spot-checks during LOCKED state.
                    pass
            elif lock.status == "LOCKED":
                if is_spot_check:
                    if active_rule_version and active_rule_version.id == locked_rule_version_id:
                        db.execute(update(RuleLock).where(RuleLock.id == lock.id).values(
                            events_since_lock=RuleLock.events_since_lock + 1,
                            events_since_mismatch=RuleLock.events_since_mismatch + 1
                        ))
                    else:
                        if lock.mismatch_count + 1 >= 5:
                            db.execute(update(RuleLock).where(RuleLock.id == lock.id).values(
                                status="SAMPLING",
                                sample_count_seen=0,
                                events_since_lock=0,
                                events_since_mismatch=0,
                                mismatch_count=0,
                                rule_version_id=None
                            ))
                        else:
                            db.execute(update(RuleLock).where(RuleLock.id == lock.id).values(
                                events_since_lock=RuleLock.events_since_lock + 1,
                                events_since_mismatch=0,
                                mismatch_count=RuleLock.mismatch_count + 1
                            ))
                else:
                    db.execute(update(RuleLock).where(RuleLock.id == lock.id).values(
                        events_since_lock=RuleLock.events_since_lock + 1,
                        events_since_mismatch=RuleLock.events_since_mismatch + 1
                    ))
        db.commit()

            
    except Exception as e:
        logger.error(f"Error processing trace {trace_id}: {e}")
        _create_dead_letter(db, trace_id, source_id, "unexpected_error", e)
    finally:
        db.close()
        event_queue.ack(record)

MAX_CONCURRENT_EVENTS = 100

async def worker_loop():
    logger.info("ULPF processing worker started. Listening for ingestion events.")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_EVENTS)

    async def _process_and_release(rec):
        try:
            await process_event(rec)
        finally:
            semaphore.release()

    while True:
        try:
            await semaphore.acquire()
            record = await event_queue.consume()
            asyncio.create_task(_process_and_release(record))
        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            semaphore.release()
            await asyncio.sleep(1)
