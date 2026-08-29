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
    
    # Process NDJSON or line-delimited logs without JSON parsing to preserve exact bytes
    if content_type in ["application/x-ndjson", "text/plain", "text/csv"] or b'\n' in body:
        lines = [line for line in body.split(b'\n') if line.strip()]
        if len(lines) > 1:
            trace_ids = []
            for line in lines:
                tid = await process_ingestion(
                    db=db,
                    source_id=source_id,
                    payload=line,
                    transport="http",
                    peer=peer
                )
                trace_ids.append(tid)
            return {"status": "accepted", "trace_ids": trace_ids}
        elif len(lines) == 1:
            body = lines[0] # Single line
            
    # Single event (or raw unstructured batch preserved as one payload)
    trace_id = await process_ingestion(
        db=db,
        source_id=source_id,
        payload=body,
        transport="http",
        peer=peer
    )
    
    return {"status": "accepted", "trace_id": trace_id}
