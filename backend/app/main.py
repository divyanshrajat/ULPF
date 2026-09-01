"""
main.py — ULPF FastAPI Application Entry Point.

Single-URL architecture:
  http://localhost:8000       → React SPA
  http://localhost:8000/api/v1/... → REST API

The compiled Vite frontend is served as static files from FastAPI.
SPA fallback ensures React Router routes work after browser refresh.
/api/* always routes to the API — never falls through to index.html.
"""
import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models.domain import Base

# ─── Router imports ────────────────────────────────────────────────────────────
from app.api.sources import router as sources_router
from app.api.files import router as files_router
from app.api.onboarding import router as onboarding_router
from app.api.review import router as review_router
from app.api.traces import router as traces_router, events_router, provenance_router
from app.api.system import router as system_router
from app.api.queries import router as queries_router
from app.api.endpoints import router as ingest_router

logger = logging.getLogger(__name__)

# ─── Startup / Shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → serve → shutdown."""
    logger.info("ULPF starting up...")

    # Ensure all tables exist (Alembic is primary; this is a safety net)
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema verified.")

    # Initialize schema registry seed data if empty
    _seed_schema_registry()

    # Start syslog server
    from app.services.ingestion.syslog_server import start_syslog_servers
    syslog_udp, syslog_tcp = await start_syslog_servers()
    app.state.syslog_udp = syslog_udp
    app.state.syslog_tcp = syslog_tcp

    # Start background worker
    from app.workers.processor import worker_loop
    app.state.worker_task = asyncio.create_task(worker_loop())

    logger.info(
        f"\n"
        f"  ╔═══════════════════════════════════════╗\n"
        f"  ║       ULPF IS READY                   ║\n"
        f"  ║  URL:  http://localhost:8000           ║\n"
        f"  ║  MODE: {settings.ULPF_MODE.upper():<30}║\n"
        f"  ║  Status: READY                         ║\n"
        f"  ╚═══════════════════════════════════════╝"
    )

    yield  # Application running

    # Shutdown
    if hasattr(app.state, "syslog_udp") and app.state.syslog_udp:
        app.state.syslog_udp.close()
    if hasattr(app.state, "syslog_tcp") and app.state.syslog_tcp:
        app.state.syslog_tcp.close()
        await app.state.syslog_tcp.wait_closed()
    if hasattr(app.state, "worker_task"):
        app.state.worker_task.cancel()
    logger.info("ULPF shutdown complete.")


# ─── App creation ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="ULPF — Universal Log Pre-processing Framework",
    description="SIH 2026 | Problem SIH26156",
    version="1.0.0-mvp",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS: only needed during Vite dev (localhost:5173 → localhost:8000).
# In production (single-origin), this is a no-op.
_dev_origins = ["http://localhost:5173"] if os.getenv("ULPF_DEV_CORS") else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routers ───────────────────────────────────────────────────────────────

API = settings.API_V1_STR

app.include_router(sources_router, prefix=API)
app.include_router(files_router, prefix=API)
app.include_router(onboarding_router, prefix=API)
app.include_router(review_router, prefix=API)
app.include_router(traces_router, prefix=API)
app.include_router(events_router, prefix=API)
app.include_router(provenance_router, prefix=API)
app.include_router(system_router, prefix=API)
app.include_router(queries_router, prefix=API)
app.include_router(ingest_router, prefix=API)

# ─── Convenience legacy aliases (backward compat) ──────────────────────────────

@app.get(f"{API}/health")
def legacy_health():
    from app.api.system import health as _health
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        return _health(db)
    finally:
        db.close()

@app.get(f"{API}/health/details")
def legacy_health_details():
    from app.api.system import health_details as _hd
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        return _hd(db)
    finally:
        db.close()

# ─── Stats endpoint (real, from DB) ───────────────────────────────────────────

@app.get(f"{API}/stats/overview")
def stats_overview():
    from app.models.domain import RawIndex, NormalizedEvent, ReviewItem, DeadLetter
    db = SessionLocal()
    try:
        ingested = db.query(RawIndex).count()
        normalized = db.query(NormalizedEvent).count()
        review_pending = db.query(ReviewItem).filter(ReviewItem.status == "PENDING").count()
        dead = db.query(DeadLetter).count()
        fast = db.query(NormalizedEvent).filter(NormalizedEvent.processing_path == "fast").count()
        adaptive = db.query(NormalizedEvent).filter(NormalizedEvent.processing_path == "adaptive").count()
        return {
            "events_ingested": ingested,
            "events_normalized": normalized,
            "events_processed": normalized + dead,
            "fast_events": fast,
            "adaptive_events": adaptive,
            "review_pending": review_pending,
            "dead_letters": dead,
            "preservation_success": ingested,
            "integrity_failures": 0,  # Would be tracked by a real audit check
        }
    finally:
        db.close()

# Keep legacy /api/v1/stats working
@app.get(f"{API}/stats")
def stats_legacy():
    return stats_overview()

# ─── Audit log endpoint ────────────────────────────────────────────────────────

@app.get(f"{API}/audit")
def list_audit(page: int = 1, page_size: int = 100):
    from app.models.domain import Audit
    db = SessionLocal()
    try:
        q = db.query(Audit).order_by(Audit.occurred_at.desc())
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "audit_id": a.audit_id,
                    "actor": a.actor,
                    "action": a.action,
                    "subject_type": a.subject_type,
                    "subject_id": a.subject_id,
                    "before": a.before,
                    "after": a.after,
                    "occurred_at": a.occurred_at.isoformat() if a.occurred_at else None,
                }
                for a in items
            ],
        }
    finally:
        db.close()

# ─── Export endpoints ──────────────────────────────────────────────────────────

@app.get(f"{API}/export/events")
def export_events_json(source_id: str = None, limit: int = 1000):
    from app.models.domain import NormalizedEvent
    db = SessionLocal()
    try:
        q = db.query(NormalizedEvent)
        if source_id:
            q = q.filter(NormalizedEvent.source_id == source_id)
        events = q.limit(limit).all()
        return [
            {
                "event_id": e.event_id,
                "trace_id": e.trace_id,
                "source_id": e.source_id,
                "schema_version": e.schema_version,
                "mapping_version": e.mapping_version,
                "processing_path": e.processing_path,
                "normalized_payload": e.normalized_payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    finally:
        db.close()


@app.get(f"{API}/export/events.ndjson")
def export_events_ndjson(source_id: str = None):
    import json
    from fastapi.responses import StreamingResponse
    from app.models.domain import NormalizedEvent
    db = SessionLocal()

    def generate():
        q = db.query(NormalizedEvent)
        if source_id:
            q = q.filter(NormalizedEvent.source_id == source_id)
        for e in q:
            row = {
                "event_id": e.event_id,
                "trace_id": e.trace_id,
                "source_id": e.source_id,
                "schema_version": e.schema_version,
                "mapping_version": e.mapping_version,
                "normalized_payload": e.normalized_payload,
            }
            yield json.dumps(row) + "\n"
        db.close()

    return StreamingResponse(generate(), media_type="application/x-ndjson",
                             headers={"Content-Disposition": 'attachment; filename="ulpf-events.ndjson"'})


# ─── Single-origin SPA serving ─────────────────────────────────────────────────

# Determine frontend dist path (works both locally and in Docker)
_FRONTEND_DIST_CANDIDATES = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist")),
    "/app/frontend/dist",
]
_frontend_dist = next((p for p in _FRONTEND_DIST_CANDIDATES if os.path.isdir(p)), None)

if _frontend_dist:
    _assets_dir = os.path.join(_frontend_dist, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend-assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(_frontend_dist, "index.html"))

    @app.middleware("http")
    async def spa_fallback(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        # Never intercept API, docs, or static asset routes
        if (
            response.status_code == 404
            and not path.startswith("/api/")
            and not path.startswith("/docs")
            and not path.startswith("/redoc")
            and not path.startswith("/assets")
            and not path.startswith("/openapi")
        ):
            return FileResponse(os.path.join(_frontend_dist, "index.html"))
        return response
else:
    @app.get("/")
    async def serve_no_frontend():
        return JSONResponse({
            "status": "backend_only",
            "message": "Frontend not built. Run 'npm run build' in frontend/ then rebuild Docker image.",
            "api_docs": "/docs",
            "api_base": settings.API_V1_STR,
        })

    logger.warning("Frontend dist not found. Serving API-only mode. Build frontend to enable single-URL serving.")


# ─── Schema registry seed ──────────────────────────────────────────────────────

def _seed_schema_registry():
    """Initialize default schema version if the registry is empty."""
    from app.models.domain import SchemaVersion
    from app.services.schema_registry.core_schema import CORE_FIELDS
    import hashlib, json
    db = SessionLocal()
    try:
        if db.query(SchemaVersion).count() == 0:
            field_def_json = json.dumps(CORE_FIELDS, sort_keys=True)
            checksum = hashlib.sha256(field_def_json.encode()).hexdigest()
            sv = SchemaVersion(
                schema_version="ulpf-core-1.0",
                field_definitions=CORE_FIELDS,
                compatibility_class="ADDITIVE",
                checksum=checksum,
            )
            db.add(sv)
            db.commit()
            logger.info("Schema registry initialized with 'ulpf-core-1.0'.")
    except Exception as e:
        logger.warning(f"Schema registry seed skipped: {e}")
    finally:
        db.close()
