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
        
        # S3 Adaptive discovery if fast path failed or format unknown
        if parsed_data is None:
            template, candidates = discover_and_extract(db, record.source_id, record.payload)
            if template:
                template_id = template.template_id
                parsed_data = {}
                for cand in candidates:
                    parsed_data[cand.field_key] = cand.sample_values[0] if cand.sample_values else None
            else:
                # Could not even discover structure -> Dead letter
                raise Exception("Format unknown and structure discovery failed")

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
