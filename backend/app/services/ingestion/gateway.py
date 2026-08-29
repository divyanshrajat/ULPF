"""
gateway.py — S1 Ingestion Gateway.

Responsibilities:
1. Accept bytes.
2. Bind source identity.
3. Allocate trace_id (ULID).
4. Write to vault (write-before-transform).
5. Write RawIndex and Trace metadata.
6. Push to internal processing queue.

Must NOT parse, normalize, or modify the payload.
"""
import ulid
from datetime import datetime
from sqlalchemy.orm import Session
from app.schemas.domain import IngestRecord
from app.services.preservation.vault import vault
from app.models.domain import RawIndex, Trace, Source
from app.core.queue import event_queue
import logging

logger = logging.getLogger(__name__)


async def process_ingestion(
    db: Session,
    source_id: str,
    payload: bytes,
    transport: str,
    peer: str = None,
    encoding_hint: str = None,
    file_id: str = None,
) -> str:
    """
    S1 Ingestion Gateway.

    Returns the allocated trace_id.
    """
    trace_id = str(ulid.new())
    received_at = datetime.utcnow()
    byte_length = len(payload)

    # 1. Write raw bytes to vault — this MUST happen before any transformation
    digest, storage_uri = await vault.write_event(
        trace_id=trace_id,
        source_id=source_id,
        payload=payload,
        received_at=received_at,
    )

    # 2. Write RawIndex record (metadata index into the vault)
    raw_idx = RawIndex(
        trace_id=trace_id,
        source_id=source_id,
        received_at=received_at,
        transport=transport,
        peer=peer,
        byte_length=byte_length,
        digest=digest,
        storage_uri=storage_uri,
    )
    db.add(raw_idx)

    # 3. Write Trace record (links trace to source and optionally to file)
    trace = Trace(
        trace_id=trace_id,
        source_id=source_id,
        file_id=file_id,
        received_at=received_at,
    )
    db.add(trace)

    # 4. Update source last_seen_at
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if source:
        source.last_seen_at = received_at

    db.commit()

    # 5. Push to async processing queue
    record = IngestRecord(
        trace_id=trace_id,
        source_id=source_id,
        payload=payload,
        byte_length=byte_length,
        received_at=received_at,
        transport=transport,
        peer=peer,
        encoding_hint=encoding_hint,
    )
    await event_queue.push(record)

    logger.info(
        f"[S1 INGESTION] trace_id={trace_id} source_id={source_id} "
        f"transport={transport} bytes={byte_length} digest={digest[:20]}..."
    )

    return trace_id
