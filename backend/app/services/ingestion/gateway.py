import ulid
from datetime import datetime
from sqlalchemy.orm import Session
from app.schemas.domain import IngestRecord
from app.services.preservation.vault import vault
from app.models.domain import RawIndex
from app.core.queue import event_queue
import logging

logger = logging.getLogger(__name__)

async def process_ingestion(
    db: Session,
    source_id: str,
    payload: bytes,
    transport: str,
    peer: str = None,
    encoding_hint: str = None
) -> str:
    """
    Handles S1 Ingestion Gateway responsibilities.
    1. Allocates trace_id
    2. Writes to vault & gets digest
    3. Writes to raw_index
    4. Pushes to internal queue
    """
    trace_id = str(ulid.new())
    received_at = datetime.utcnow()
    byte_length = len(payload)
    
    # 1. Write to vault
    digest, storage_uri = await vault.write_event(
        trace_id=trace_id,
        source_id=source_id,
        payload=payload,
        received_at=received_at
    )
    
    # 2. Write to raw_index database
    raw_idx = RawIndex(
        trace_id=trace_id,
        source_id=source_id,
        received_at=received_at,
        transport=transport,
        peer=peer,
        byte_length=byte_length,
        digest=digest,
        storage_uri=storage_uri
    )
    db.add(raw_idx)
    db.commit()
    
    # 3. Create IngestRecord and push to queue
    record = IngestRecord(
        trace_id=trace_id,
        source_id=source_id,
        payload=payload,
        byte_length=byte_length,
        received_at=received_at,
        transport=transport,
        peer=peer,
        encoding_hint=encoding_hint
    )
    
    # For HTTP/TCP we can await push to apply backpressure.
    await event_queue.push(record)
    
    logger.info(f"Ingested event trace_id={trace_id} source_id={source_id} transport={transport}")
    
    return trace_id
