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
        role = x_ulpf_role or "viewer"
        return {"username": x_ulpf_user, "role": role}

    # Default: unauthenticated viewer (read-only). Mutations require login.
    return {"username": "anonymous", "role": "viewer"}


def require_role(required_role: str):
    """Dependency factory: require minimum role."""
    role_order = ["viewer", "approver", "administrator"]

    def _check(user: dict = Depends(get_current_user)):
        user_role = user.get("role", "viewer")
        if role_order.index(user_role) < role_order.index(required_role):
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
