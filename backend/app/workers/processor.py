import asyncio
import logging
from app.core.queue import event_queue
from app.core.database import SessionLocal
from app.services.detection.classifier import classify_format
from app.services.extraction.deterministic import parse_json, parse_key_value, parse_delimited, parse_syslog_3164
from app.services.discovery.extraction_service import discover_and_extract
from app.services.typing.inference import infer_value_type
from app.services.mapping.semantic import semantic_mapper
from app.services.normalization.engine import normalization_engine
from app.services.provenance.layer import save_provenance
from app.models.domain import DeadLetter, RawIndex
from datetime import datetime
from app.core.opensearch import get_opensearch_client, index_event
import json

logger = logging.getLogger(__name__)

async def process_event(record):
    db = SessionLocal()
    try:
        # S2 Format Detection
        detection = classify_format(record.payload)
        
        parsed_data = None
        template_id = None
        
        # Fast path parsing for known formats
        if detection.confidence >= 0.90:
            if detection.format_name == "json":
                parsed_data = parse_json(record.payload)
            elif detection.format_name == "key_value":
                parsed_data = parse_key_value(record.payload)
            elif detection.format_name == "syslog_3164":
                parsed_data = parse_syslog_3164(record.payload)
            elif detection.format_name == "delimited_pipe":
                parsed_data = parse_delimited(record.payload, delimiter='|')
                
            if parsed_data:
                # Derive a stable template_id based on keys
                import hashlib
                keys = sorted(parsed_data.keys())
                keys_str = ",".join(keys)
                key_hash = hashlib.md5(keys_str.encode()).hexdigest()[:12]
                template_id = f"tpl_{record.source_id}_fp_{key_hash}"
        
        # S3 Adaptive discovery if fast path failed or format unknown
        if parsed_data is None:
            template, candidates = discover_and_extract(db, record.source_id, record.payload)
            if template:
                template_id = template.template_id
                parsed_data = {}
                for cand in candidates:
                    parsed_data[cand.field_key] = cand.sample_values[0] if cand.sample_values else None
                pattern = template.pattern
            else:
                # Could not even discover structure -> Dead letter
                raise Exception("Format unknown and structure discovery failed")
        else:
            # For fast path, generate candidates from parsed_data
            from app.schemas.domain import CandidateField
            candidates = []
            for k, v in parsed_data.items():
                candidates.append(CandidateField(field_key=k, position="0", sample_values=[str(v)]))
            pattern = f"FastPath:{detection.format_name}"
            
            # Create a mock template in DB if it doesn't exist just so we can attach mappings
            from app.models.domain import Template
            template = db.query(Template).filter(Template.template_id == template_id).first()
            if not template:
                template = Template(
                    template_id=template_id,
                    source_id=record.source_id,
                    pattern=pattern,
                    variable_positions={},
                    occurrence_count=1
                )
                db.add(template)
                db.commit()

        # Check if mapping exists
        from app.models.domain import Mapping, ReviewItem
        import ulid
        active_mapping = db.query(Mapping).filter(Mapping.source_id == record.source_id, Mapping.template_id == template_id, Mapping.status == "active").first()
        
        if not active_mapping:
            # Check if already pending review
            pending_review = db.query(ReviewItem).filter(ReviewItem.source_id == record.source_id, ReviewItem.template_id == template_id, ReviewItem.status == "pending").first()
            if not pending_review:
                proposals = []
                for cand in candidates:
                    cand.inferred_type = infer_value_type(cand.sample_values)
                    props = semantic_mapper.propose_mappings(db, record.source_id, template_id, cand, pattern)
                    if props:
                        proposals.append({
                            "source_field": cand.field_key,
                            "position": cand.position,
                            "inferred_type": cand.inferred_type,
                            "sample_value": cand.sample_values[0] if cand.sample_values else None,
                            "proposed_target": props[0].target_field,
                            "confidence": props[0].confidence,
                            "decision": props[0].decision,
                            "signals": props[0].signals
                        })
                
                review_item = ReviewItem(
                    review_id=str(ulid.new()),
                    source_id=record.source_id,
                    template_id=template_id,
                    pattern=pattern,
                    proposals=proposals
                )
                db.add(review_item)
                db.commit()
        else:
            # Drift Detection: active mapping exists, check for unmapped keys
            unmapped_candidates = []
            for cand in candidates:
                if cand.field_key not in active_mapping.field_bindings:
                    unmapped_candidates.append(cand)
            
            if unmapped_candidates:
                # Check if drift is already in review
                drift_template_id = f"{template_id}_drift"
                pending_drift = db.query(ReviewItem).filter(ReviewItem.source_id == record.source_id, ReviewItem.template_id == drift_template_id, ReviewItem.status == "pending").first()
                if not pending_drift:
                    proposals = []
                    for cand in unmapped_candidates:
                        cand.inferred_type = infer_value_type(cand.sample_values)
                        props = semantic_mapper.propose_mappings(db, record.source_id, template_id, cand, pattern)
                        if props:
                            proposals.append({
                                "source_field": cand.field_key,
                                "position": cand.position,
                                "inferred_type": cand.inferred_type,
                                "sample_value": cand.sample_values[0] if cand.sample_values else None,
                                "proposed_target": props[0].target_field,
                                "confidence": props[0].confidence,
                                "decision": props[0].decision,
                                "signals": props[0].signals
                            })
                    if proposals:
                        review_item = ReviewItem(
                            review_id=str(ulid.new()),
                            source_id=record.source_id,
                            template_id=drift_template_id,
                            pattern=f"DRIFT: {pattern}",
                            proposals=proposals
                        )
                        db.add(review_item)
                        db.commit()

        # Fetch actual digest
        raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == record.trace_id).first()
        digest = raw_idx.digest if raw_idx else "sha256:unknown"

        # Create raw_ref dictionary
        raw_ref = {
            "trace_id": record.trace_id,
            "digest": digest,
            "byte_length": record.byte_length
        }

        # S4 Normalization
        normalized_event, provenance_records = normalization_engine.normalize(
            db=db,
            parsed_data=parsed_data,
            source_id=record.source_id,
            template_id=template_id,
            trace_id=record.trace_id,
            raw_ref=raw_ref
        )
        
        # S6 Save Provenance
        save_provenance(db, provenance_records)
        
        # Output (OpenSearch sink)
        os_client = get_opensearch_client()
        event_dict = normalized_event.dict()
        event_dict["trace_id"] = record.trace_id
        event_dict["source_id"] = record.source_id
        event_dict["@timestamp"] = datetime.utcnow().isoformat()
        index_event(os_client, event_dict)
        
        logger.info(f"Successfully processed {record.trace_id}")
        
    except Exception as e:
        logger.error(f"Error processing {record.trace_id}: {e}")
        dl = DeadLetter(
            trace_id=record.trace_id,
            stage="processing",
            error_class=e.__class__.__name__,
            diagnostic=str(e),
            raw_reference=f"vault://{record.source_id}/.../{record.trace_id}.raw",
            occurred_at=datetime.utcnow()
        )
        db.add(dl)
        db.commit()
    finally:
        db.close()
        event_queue.task_done()

async def worker_loop():
    logger.info("Starting processing worker...")
    while True:
        record = await event_queue.pop()
        await process_event(record)
