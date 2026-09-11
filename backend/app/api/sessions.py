import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import IngestionSession, RuleLock, RawIndex, UnresolvedEvent, RuleVersion
from app.core.queue import event_queue, EventRecord
from app.services.preservation.vault import vault
from app.services.rules.fingerprint import generate_fingerprint
from app.services.rules.parsers.factory import ParserFactory
from app.services.rules.registry import find_active_rule_by_fingerprint
import random

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("")
def list_sessions(
    source_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(IngestionSession)
    if source_id:
        query = query.filter(IngestionSession.source_id == source_id)
        
    total = query.count()
    sessions = query.order_by(desc(IngestionSession.started_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    from app.models.domain import Rule, RuleVersion
    items = []
    for session in sessions:
        lock = db.query(RuleLock).filter(RuleLock.session_id == session.id).first()
        rule_name = None
        if lock and lock.rule_version_id:
            rv = db.query(RuleVersion).filter(RuleVersion.id == lock.rule_version_id).first()
            if rv:
                rule = db.query(Rule).filter(Rule.rule_id == rv.rule_id).first()
                if rule:
                    rule_name = f"{rule.name}@{rv.version}"
        
        sess_dict = {
            "id": session.id,
            "source_id": session.source_id,
            "status": session.status,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "total_events": session.total_events,
            "processed_events": session.processed_events,
            "normalized_count": session.normalized_count,
            "unresolved_count": session.unresolved_count,
            "lock": {
                "status": lock.status,
                "sample_count_seen": lock.sample_count_seen,
                "mismatch_count": lock.mismatch_count,
                "rule_name": rule_name
            } if lock else None
        }
        items.append(sess_dict)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(IngestionSession).filter(IngestionSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    rule_lock = db.query(RuleLock).filter(RuleLock.session_id == session.id).first()
    
    return {
        "id": session.id,
        "source_id": session.source_id,
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "locked_rule": {
            "rule_version_id": rule_lock.rule_version_id if rule_lock else None,
            "locked_at": rule_lock.created_at if rule_lock else None
        },
        "progress": {
            "total": session.total_events,
            "processed": session.processed_events,
            "normalized": session.normalized_count,
            "unresolved": session.unresolved_count
        }
    }

from app.api.api_keys import verify_api_key, require_source_scope
from app.models.domain import ApiKey

@router.post("")
def create_session(payload: dict[str, Any], db: Session = Depends(get_db), api_key: ApiKey = Depends(verify_api_key)):
    source_id = payload.get("source_id")
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id required")
        
    require_source_scope(api_key, source_id)
        
    session_id = str(uuid.uuid4())
    session = IngestionSession(
        id=session_id,
        source_id=source_id,
        status="ACTIVE",
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    return {"id": session.id, "status": session.status}

@router.post("/{session_id}/events")
async def submit_events(session_id: str, events: list[str], db: Session = Depends(get_db), api_key: ApiKey = Depends(verify_api_key)):
    session = db.query(IngestionSession).filter(IngestionSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    require_source_scope(api_key, session.source_id)
        
    session.total_events += len(events)
    db.commit()

    lock = db.query(RuleLock).filter(RuleLock.session_id == session_id).first()
    if not lock:
        lock = RuleLock(id=str(uuid.uuid4()), session_id=session_id, status="SAMPLING")
        db.add(lock)

    normalized_counter = 0
    unresolved_counter = 0
    processed_counter = 0
    batch_records = []

    for i, line in enumerate(events):
        line = line.strip()
        if not line:
            continue
            
        trace_id = str(uuid.uuid4())
        payload = line.encode('utf-8')
        received_at = datetime.utcnow()
        
        digest_str, vault_path = await vault.write_event(
            trace_id=trace_id,
            source_id=session.source_id,
            payload=payload,
            received_at=received_at
        )

        raw_idx = RawIndex(
            trace_id=trace_id,
            source_id=session.source_id,
            transport="stream_api",
            byte_length=len(payload),
            digest=digest_str,
            storage_uri=vault_path,
            received_at=received_at,
            session_id=session_id
        )
        db.add(raw_idx)
        
        fingerprint = generate_fingerprint(line)
        is_unresolved = False
        
        if lock.status == "SAMPLING":
            active_rule = find_active_rule_by_fingerprint(db, fingerprint)
            if active_rule:
                try:
                    parser = ParserFactory.create(active_rule.parser_type, active_rule.parser_definition, active_rule.field_mappings)
                    parsed = parser.parse(line)
                    missing = [f for f in active_rule.required_fields if f not in parsed] if active_rule.required_fields else []
                    if missing:
                        is_unresolved = True
                    else:
                        if not lock.rule_version_id:
                            lock.rule_version_id = active_rule.id
                            lock.fingerprint = fingerprint
                        lock.sample_count_seen += 1
                        if lock.sample_count_seen >= 3:
                            lock.status = "LOCKED"
                except Exception:
                    is_unresolved = True
            else:
                is_unresolved = True
        elif lock.status == "LOCKED":
            lock.events_since_lock += 1
            # Adaptive spot-check rate table (impl §7)
            if lock.mismatch_count > 0 and lock.events_since_mismatch < 50:
                spot_check_rate = 25
            elif lock.events_since_lock < 100:
                spot_check_rate = 50
            else:
                spot_check_rate = 500
            lock.events_since_mismatch += 1

            if random.randint(1, spot_check_rate) == 1:
                active_rule = db.query(RuleVersion).filter(RuleVersion.id == lock.rule_version_id).first()
                if active_rule:
                    try:
                        parser = ParserFactory.create(active_rule.parser_type, active_rule.parser_definition, active_rule.field_mappings)
                        parsed = parser.parse(line)
                        missing = [f for f in active_rule.required_fields if f not in parsed] if active_rule.required_fields else []
                        if missing:
                            is_unresolved = True
                    except Exception:
                        is_unresolved = True
                else:
                    is_unresolved = True
                    
                if is_unresolved:
                    lock.mismatch_count += 1
                    lock.events_since_mismatch = 0  # reset; rate will tighten to 1-in-25
                    if lock.mismatch_count >= 5:
                        lock.status = "SAMPLING"
                        lock.sample_count_seen = 0
                        lock.events_since_lock = 0
                        lock.events_since_mismatch = 0
        
        if is_unresolved:
            unres = UnresolvedEvent(id=str(uuid.uuid4()), trace_id=trace_id, fingerprint=fingerprint, session_id=session_id)
            db.add(unres)
            unresolved_counter += 1
        else:
            normalized_counter += 1
            record = EventRecord(
                trace_id=trace_id,
                source_id=session.source_id,
                payload=payload,
                byte_length=len(payload)
            )
            batch_records.append(record)
            
        processed_counter += 1
        if i % 100 == 0:
            db.commit()
            for r in batch_records:
                await event_queue.publish(r)
            batch_records.clear()
    db.commit()
    for r in batch_records:
        await event_queue.publish(r)

    # Re-fetch session to update it safely outside the loop
    session = db.query(IngestionSession).filter(IngestionSession.id == session_id).first()
    if session:
        session.processed_events += processed_counter
        session.normalized_count += normalized_counter
        session.unresolved_count += unresolved_counter
        db.commit()

    return {
        "status": "ACCEPTED",
        "events_count": len(events)
    }
