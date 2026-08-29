from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.ingestion.gateway import process_ingestion
from typing import List, Union, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest")
async def ingest_events(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Ingest a single event or batch of events via HTTP POST.
    Source must be identified via X-ULPF-Source-ID header.
    """
    source_id = request.headers.get("X-ULPF-Source-ID")
    if not source_id:
        raise HTTPException(status_code=400, detail={"code": "MISSING_SOURCE_ID", "message": "X-ULPF-Source-ID header required", "stage": "ingestion", "trace_id": None, "details": {}})

    # Check if source exists and is active
    from app.models.domain import Source
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail={"code": "SOURCE_NOT_FOUND", "message": f"Source '{source_id}' not found", "stage": "ingestion", "trace_id": None, "details": {}})
    if source.status != "active":
        raise HTTPException(status_code=403, detail={"code": "SOURCE_INACTIVE", "message": f"Source '{source_id}' is not active (status: {source.status})", "stage": "ingestion", "trace_id": None, "details": {}})

    # Helper to extract exact bytes of objects within a JSON array
    def extract_json_objects_from_array(body_bytes: bytes) -> List[bytes]:
        objects = []
        depth = 0
        in_string = False
        escape = False
        start_idx = -1
        
        for i in range(len(body_bytes)):
            char = body_bytes[i:i+1]
            if escape:
                escape = False
                continue
            if char == b'\\':
                escape = True
                continue
            if char == b'"':
                in_string = not in_string
                continue
                
            if not in_string:
                if char == b'{':
                    if depth == 0:
                        start_idx = i
                    depth += 1
                elif char == b'}':
                    depth -= 1
                    if depth == 0 and start_idx != -1:
                        objects.append(body_bytes[start_idx:i+1])
                        start_idx = -1
        return objects

    content_type = request.headers.get("Content-Type", "")
    body = await request.body()
    peer = request.client.host if request.client else None
    
    # Process batch payloads without json.loads to preserve exact bytes
    payloads = []
    
    body_stripped = body.strip()
    if body_stripped.startswith(b'[') and body_stripped.endswith(b']'):
        # JSON Array
        payloads = extract_json_objects_from_array(body)
    elif content_type in ["application/x-ndjson", "text/plain", "text/csv"] or b'\n' in body:
        # Line delimited
        payloads = [line for line in body.split(b'\n') if line.strip()]
    else:
        # Single event
        payloads = [body]
        
    trace_ids = []
    for p in payloads:
        tid = await process_ingestion(
            db=db,
            source_id=source_id,
            payload=p,
            transport="http",
            peer=peer
        )
        trace_ids.append(tid)
        
    if len(trace_ids) == 1:
        return {"status": "accepted", "trace_id": trace_ids[0]}
    
    return {"status": "accepted", "trace_ids": trace_ids}

