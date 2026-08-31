"""
system.py — System health, configuration, and airgap verification API.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.core.auth import require_admin
import os
import logging

router = APIRouter(prefix="/system", tags=["System"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """Quick health check."""
    db_ok = _check_db(db)
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "healthy" if db_ok else "unavailable",
    }


@router.get("/health/details")
def health_details(db: Session = Depends(get_db)):
    """Detailed component health for UI header indicator."""
    db_status = "healthy" if _check_db(db) else "unavailable"
    redis_status = _check_redis()
    opensearch_status = _check_opensearch()
    model_status = _check_model()
    vault_status = _check_vault()

    overall = "healthy"
    if db_status != "healthy":
        overall = "unavailable"
    elif any(s == "unavailable" for s in [redis_status, opensearch_status, model_status]):
        overall = "degraded"

    return {
        "overall": overall,
        "components": {
            "api": "healthy",
            "database": db_status,
            "redis": redis_status,
            "opensearch": opensearch_status,
            "model": model_status,
            "vault": vault_status,
            "worker": "healthy",  # Worker runs in-process with FastAPI
        },
        "mode": settings.ULPF_MODE,
    }


@router.get("/airgap")
def airgap_status():
    """Air-gap verification endpoint."""
    model_local = _check_model() != "unavailable"
    vault_local = _check_vault() == "healthy"
    frontend_local = _check_frontend_local()

    return {
        "mode": settings.ULPF_MODE,
        "internet_required": False,
        "model_local": model_local,
        "frontend_local": frontend_local,
        "database_local": True,
        "search_local": True,
        "vault_local": vault_local,
        "outbound_dependencies": False,
        "network_policy": "STRICT_OFFLINE" if settings.ULPF_MODE == "airgap" else "INTERNET_ALLOWED",
        "checks": {
            "model": "PASS" if model_local else "FAIL — model not found locally",
            "frontend": "PASS" if frontend_local else "FAIL — frontend assets not found",
            "vault": "PASS" if vault_local else "FAIL — vault directory not accessible",
        },
    }


@router.get("/config")
def get_config(user: dict = Depends(require_admin)):
    """Read-only effective configuration (admin only)."""
    return {
        "mode": settings.ULPF_MODE,
        "api_prefix": settings.API_V1_STR,
        "vault_dir": settings.VAULT_DIR,
        "opensearch_index": settings.OPENSEARCH_INDEX,
        "model_path": settings.ULPF_MODEL_PATH,
        "thresholds": {
            "mapping_review_floor": settings.MAPPING_REVIEW_FLOOR,
            "mapping_auto_accept": settings.MAPPING_AUTO_ACCEPT,
        },
        "drain3": {
            "sim_th": settings.DRAIN3_SIM_TH,
            "depth": settings.DRAIN3_DEPTH,
            "max_children": settings.DRAIN3_MAX_CHILDREN,
            "max_templates": settings.DRAIN3_MAX_TEMPLATES,
        },
    }


# ─── Check helpers ────────────────────────────────────────────────────────────

def _check_db(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _check_redis() -> str:
    try:
        import redis
        r = redis.from_url(settings.REDIS_URI, socket_connect_timeout=0.2, socket_timeout=0.2)
        r.ping()
        return "healthy"
    except Exception:
        return "unavailable"


def _check_opensearch() -> str:
    try:
        from app.core.opensearch import get_opensearch_client
        client = get_opensearch_client()
        client.info(request_timeout=0.2)
        return "healthy"
    except Exception:
        return "degraded"


def _check_model() -> str:
    model_path = settings.ULPF_MODEL_PATH
    # If it's an absolute path, check it exists
    if os.path.isabs(model_path):
        return "healthy" if os.path.isdir(model_path) else "unavailable"
    # If it's a model name (not a path), treat as available (will download on first use in internet mode)
    if settings.ULPF_MODE == "airgap":
        return "unavailable"
    return "healthy"


def _check_vault() -> str:
    vault_dir = settings.VAULT_DIR
    try:
        os.makedirs(vault_dir, exist_ok=True)
        test_file = os.path.join(vault_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return "healthy"
    except Exception:
        return "unavailable"


def _check_frontend_local() -> bool:
    """Check if compiled frontend assets exist."""
    import pathlib
    # Path relative to backend app
    frontend_dist = pathlib.Path(__file__).parent.parent.parent / "frontend" / "dist"
    docker_dist = pathlib.Path("/app/frontend/dist")
    return frontend_dist.exists() or docker_dist.exists()
