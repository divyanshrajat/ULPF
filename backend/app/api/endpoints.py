from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ingestion.gateway import process_ingestion
from typing import List, Union, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest")
async def ingest_events(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Ingest a single event or batch of events via HTTP POST.
    """
    # Simple auth check can be added here
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    source_id = request.headers.get("X-ULPF-Source-ID")
    if not source_id:
        raise HTTPException(status_code=400, detail="Missing X-ULPF-Source-ID header")
    
    # Check if source exists
    from app.models.domain import Source
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status != "active":
        raise HTTPException(status_code=403, detail="Source is not active")

    content_type = request.headers.get("Content-Type", "")
    
    # We read the raw body
    body = await request.body()
    peer = request.client.host if request.client else None
    
    # If JSON array (batch) we could split it, but for raw lossless preservation,
    # the gateway expects one payload = one event. If they send an array of JSON objects,
    # we should ideally parse it and save each object as a raw event, or save the batch
    # as a single raw event and split during processing. The TRD says "Accept single object or array; 
    # acknowledge only after vault write completes". 
    # For MVP simplicity, we will assume one HTTP request payload = one event, unless it's a JSON array.
    import json
    try:
        if content_type == "application/json":
            data = json.loads(body)
            if isinstance(data, list):
                # Batch ingestion
                trace_ids = []
                for item in data:
                    item_payload = json.dumps(item).encode("utf-8")
                    tid = await process_ingestion(
                        db=db,
                        source_id=source_id,
                        payload=item_payload,
                        transport="http",
                        peer=peer,
                        encoding_hint="utf-8"
                    )
                    trace_ids.append(tid)
                return {"status": "accepted", "trace_ids": trace_ids}
    except Exception as e:
        logger.warning(f"Failed to parse JSON batch: {e}")
        # fallback to single raw payload
        pass

    # Single event
    trace_id = await process_ingestion(
        db=db,
        source_id=source_id,
        payload=body,
        transport="http",
        peer=peer
    )
    
    return {"status": "accepted", "trace_id": trace_id}
