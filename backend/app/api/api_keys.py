import hashlib
import secrets
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import ApiKey

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

@router.get("")
def list_api_keys(db: Session = Depends(get_db)):
    keys = db.query(ApiKey).order_by(desc(ApiKey.created_at)).all()
    return keys

@router.post("")
def create_api_key(payload: dict[str, Any], db: Session = Depends(get_db)):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
        
    source_scope = payload.get("source_scope", "*")
    environment = payload.get("environment", "production")
    
    raw_key = f"ulpf_{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)
    masked = f"ulpf_...{raw_key[-4:]}"
    
    api_key = ApiKey(
        id=str(uuid.uuid4()),
        key_hash=key_hash,
        masked_key=masked,
        name=name,
        source_scope=source_scope,
        environment=environment,
        status="active"
    )
    db.add(api_key)
    db.commit()
    
    return {
        "id": api_key.id,
        "name": api_key.name,
        "raw_key": raw_key, # Return only once
        "masked_key": api_key.masked_key,
        "source_scope": api_key.source_scope,
        "environment": api_key.environment
    }

@router.delete("/{key_id}")
def revoke_api_key(key_id: str, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    api_key.status = "revoked"
    db.commit()
    return {"status": "revoked"}
