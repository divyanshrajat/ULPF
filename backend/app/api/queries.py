from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import Mapping, RawIndex, Provenance, DeadLetter, Source, ReviewItem
from app.core.opensearch import get_opensearch_client

router = APIRouter()

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    events_ingested = db.query(RawIndex).count()
    dead_letters = db.query(DeadLetter).count()
    # Mocking normalized since we don't store it in PG, and we can fetch from OS or assume ingested - DL
    events_normalized = events_ingested - dead_letters
    review_queue_count = db.query(ReviewItem).filter(ReviewItem.status == "pending").count()
    return {
        "events_ingested": events_ingested,
        "events_normalized": max(0, events_normalized),
        "review_queue": review_queue_count,
        "dead_letters": dead_letters
    }

@router.get("/mappings")
async def list_mappings(db: Session = Depends(get_db)):
    mappings = db.query(Mapping).all()
    return mappings

@router.get("/events")
async def list_events():
    client = get_opensearch_client()
    try:
        response = client.search(
            index="ulpf-events",
            body={
                "query": {"match_all": {}},
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": 50
            }
        )
        return [hit["_source"] for hit in response["hits"]["hits"]]
    except Exception as e:
        return []

@router.get("/events/{trace_id}/raw")
async def get_raw_event(trace_id: str, db: Session = Depends(get_db)):
    from app.services.preservation.vault import vault
    raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
    if not raw_idx:
        return {"error": "Not found"}
    payload = await vault.read_event(raw_idx.source_id, raw_idx.received_at, trace_id)
    verified = vault.verify_digest(payload, raw_idx.digest)
    return {
        "payload": payload.decode('utf-8', errors='ignore'),
        "digest": raw_idx.digest,
        "verified": verified
    }

@router.get("/events/{trace_id}/provenance")
async def get_provenance(trace_id: str, db: Session = Depends(get_db)):
    provs = db.query(Provenance).filter(Provenance.trace_id == trace_id).all()
    return provs

@router.get("/sources")
async def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return sources

@router.get("/deadletters")
async def list_deadletters(db: Session = Depends(get_db)):
    dl = db.query(DeadLetter).all()
    return dl

