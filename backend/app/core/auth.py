"""
auth.py — Local lightweight authentication for SIH MVP.

Supports:
  - HTTP Basic auth via X-ULPF-Token header (hashed password comparison).
  - Role-based access: viewer | approver | administrator.
  - Backend always produces a real actor identity; no hardcoded "demo-admin" in business logic.
"""
from fastapi import Header, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import hashlib
import secrets
from app.core.config import settings

security = HTTPBasic(auto_error=False)

# For SIH MVP: single configured admin user.
# In production, replace with database-backed user management.
_USERS = {
    settings.ADMIN_USERNAME: {
        "password_hash": hashlib.sha256(settings.ADMIN_PASSWORD.encode()).hexdigest(),
        "role": "administrator",
    }
}

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def get_current_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
    x_ulpf_user: Optional[str] = Header(None, alias="X-ULPF-User"),
    x_ulpf_role: Optional[str] = Header(None, alias="X-ULPF-Role"),
) -> dict:
    """
    Authenticate request.
    Priority: HTTP Basic > header-based (legacy dev path).
    """
    if credentials and credentials.username:
        user = _USERS.get(credentials.username)
        if user:
            pw_hash = _hash_password(credentials.password or "")
            if secrets.compare_digest(pw_hash, user["password_hash"]):
                return {"username": credentials.username, "role": user["role"]}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Legacy header-based auth (dev convenience, used only when no Basic creds)
    if x_ulpf_user:
        raw_role = (x_ulpf_role or "viewer").lower()
        role = "administrator" if raw_role in ("admin", "administrator") else raw_role
        return {"username": x_ulpf_user, "role": role}

    # Default: unauthenticated viewer (read-only). Mutations require login.
    return {"username": "anonymous", "role": "viewer"}


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
