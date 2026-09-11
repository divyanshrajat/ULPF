"""
auth.py — Local lightweight authentication for SIH MVP.

Supports:
  - HTTP Basic auth via X-ULPF-Token header (hashed password comparison).
  - Role-based access: viewer | approver | administrator.
  - Backend always produces a real actor identity; no hardcoded "demo-admin" in business logic.
"""
import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
import base64
import time
import json
import hmac

from app.core.config import settings

security = HTTPBasic(auto_error=False)
bearer_security = HTTPBearer(auto_error=False)

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(username: str, role: str, tenant_id: str) -> str:
    """Create a simple HMAC-SHA256 signed JWT-like token"""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
    
    payload_dict = {
        "sub": username,
        "role": role,
        "tenant_id": tenant_id,
        "exp": int(time.time()) + 3600  # 1 hour expiration
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    
    signature_input = f"{header}.{payload}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        signature_input.encode(),
        hashlib.sha256
    ).digest()
    
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{signature_input}.{sig_b64}"


def verify_access_token(token: str) -> dict | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    
    header, payload, sig = parts
    
    signature_input = f"{header}.{payload}"
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode(),
        signature_input.encode(),
        hashlib.sha256
    ).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
    
    if not secrets.compare_digest(sig, expected_sig_b64):
        return None
        
    pad = len(payload) % 4
    if pad:
        payload += "=" * (4 - pad)
        
    try:
        decoded = json.loads(base64.urlsafe_b64decode(payload).decode())
        if decoded.get("exp", 0) < time.time():
            return None
        return decoded
    except Exception:
        return None


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPBasicCredentials | None = Depends(security),
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_security)
) -> dict:
    """
    Authenticate request.
    Supports Bearer token (JWT) or HTTP Basic credentials.
    """
    # 1. Try Bearer token first
    if bearer and type(bearer).__name__ != "Depends" and bearer.credentials:
        payload = verify_access_token(bearer.credentials)
        if payload and payload.get("sub"):
            return {
                "username": payload["sub"], 
                "role": payload.get("role", "viewer"),
                "tenant_id": payload.get("tenant_id", "default")
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Fallback to Basic Auth (used by API keys usually, or legacy scripts)
    if credentials and type(credentials).__name__ != "Depends" and credentials.username:
        user = db.query(User).filter(User.username == credentials.username).first()
        if user and verify_password(credentials.password or "", user.password_hash):
            return {"username": user.username, "role": user.role, "tenant_id": user.tenant_id}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Default: unauthenticated viewer (read-only). Mutations require login.
    return {"username": "anonymous", "role": "viewer", "tenant_id": "default"}


def require_role(required_role: str):
    """Dependency factory: require minimum role."""
    role_order = ["viewer", "approver", "administrator"]
    role_aliases = {"admin": "administrator"}

    def _check(user: dict = Depends(get_current_user)):
        user_role = user.get("role", "viewer")
        normalized_role = role_aliases.get(user_role, user_role)
        normalized_req = role_aliases.get(required_role, required_role)
        
        try:
            user_idx = role_order.index(normalized_role)
            req_idx = role_order.index(normalized_req)
        except ValueError:
            user_idx = 0
            req_idx = 1

        if user_idx < req_idx:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required; current role is '{user_role}'",
            )
        return user

    return _check


def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return user


def require_approver(user: dict = Depends(get_current_user)):
    if user.get("role") not in ("approver", "administrator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approver or administrator privileges required",
        )
    return user
