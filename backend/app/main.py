import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.api_keys import router as api_keys_router
from app.api.events import router as events_router
from app.api.jobs import router as jobs_router
from app.api.onboarding import router as onboarding_router
from app.api.rules import router as rules_router
from app.api.sessions import router as sessions_router
from app.api.sources import router as sources_router
from app.core.config import settings

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Universal Log Pre-processing Framework (ULPF) V2 - API"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, SessionLocal
from app.models.domain import NormalizedEvent, UnresolvedEvent, DeadLetter, Rule, Source, RuleVersion, RuleFingerprint
from app.services.rules.fingerprint import generate_fingerprint
from app.workers.processor import worker_loop
import redis as redis_lib
from app.core.opensearch import get_opensearch_client

@app.on_event("startup")
async def startup_event():
    logger.info("Starting ULPF API Server...")
    
    # Start the worker loop in the background
    asyncio.create_task(worker_loop())
    
    # Seed demo data idempotently
    if settings.ULPF_SEED_DEMO_DATA:
        try:
            db = SessionLocal()
            from passlib.context import CryptContext
            import uuid
            from app.models.domain import User
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            if not db.query(User).filter(User.username == "analyst").first():
                db.add(User(
                    id=str(uuid.uuid4()),
                    tenant_id="default",
                    username="analyst",
                    password_hash=pwd_context.hash("ulpf-admin"),
                    role="approver"
                ))
                
            if not db.query(User).filter(User.username == "auditor").first():
                db.add(User(
                    id=str(uuid.uuid4()),
                    tenant_id="default",
                    username="auditor",
                    password_hash=pwd_context.hash("ulpf-admin"),
                    role="viewer"
                ))
            
            
            # Check and create paloalto source
            if not db.query(Source).filter(Source.source_id == "paloalto").first():
                pa = Source(
                    source_id="paloalto",
                    name="Palo Alto firewall — no matching rule",
                    vendor="Palo Alto Networks"
                )
                db.add(pa)
                
            # Check and create cloudtrail source, rule, version, fingerprint
            if not db.query(Source).filter(Source.source_id == "cloudtrail").first():
                ct = Source(
                    source_id="cloudtrail",
                    name="AWS CloudTrail — matches existing rule",
                    vendor="AWS"
                )
                db.add(ct)
                
                rule_id = "rule-cloudtrail-01"
                rule = Rule(
                    rule_id=rule_id,
                    name="CloudTrail Login Event",
                    status="ACTIVE"
                )
                db.add(rule)
            
                rule_ver = RuleVersion(
                    id=f"{rule_id}-v1",
                    rule_id=rule_id,
                    version=1,
                    parser_type="jsonpath",
                    parser_definition={"paths": {
                        "userIdentity.arn": "$.userIdentity.arn",
                        "sourceIPAddress": "$.sourceIPAddress",
                        "eventName": "$.eventName",
                        "eventTime": "$.eventTime"
                    }},
                    field_mappings={
                        "userIdentity.arn": "user.id", 
                        "sourceIPAddress": "src_endpoint.ip",
                        "eventName": "activity_name",
                        "eventTime": "time"
                    },
                    target_schema="ecs",
                    schema_version="1.0",
                    rule_hash="abc123hash",
                    status="ACTIVE"
                )
                db.add(rule_ver)
            
                # Generate fingerprint from the cloudtrail sample
                sample_ct = '{"eventTime":"2026-09-07T09:58:03Z","eventSource":"iam.amazonaws.com","eventName":"ConsoleLogin","sourceIPAddress":"198.51.100.22","userIdentity":{"arn":"arn:aws:iam::4021:user/asha"}}'
                fp = generate_fingerprint(sample_ct, vendor_token="cloudtrail")
                rule_fp = RuleFingerprint(
                    id=f"fp-{rule_id}",
                    rule_id=rule_id,
                    fingerprint=fp
                )
                db.add(rule_fp)
            
            db.commit()
        except Exception as e:
            logger.error(f"Failed to seed demo data: {e}")
        finally:
            db.close()

from app.api.auth import router as auth_router

# API Routers
API = "/api/v1"
app.include_router(auth_router, prefix=API)
app.include_router(sources_router, prefix=API)
app.include_router(onboarding_router, prefix=API)
app.include_router(rules_router, prefix=API)
app.include_router(events_router, prefix=API)
app.include_router(jobs_router, prefix=API)
app.include_router(sessions_router, prefix=API)
app.include_router(api_keys_router, prefix=API)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/v1/health")
def health_check_v1():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/v1/stats/overview")
def get_stats_overview(db: Session = Depends(get_db)):
    events_normalized = db.query(NormalizedEvent).count()
    events_processed = events_normalized
    fast_events = db.query(NormalizedEvent).filter(NormalizedEvent.processing_path == 'fast_path').count()
    adaptive_events = db.query(NormalizedEvent).filter(NormalizedEvent.processing_path != 'fast_path').count()
    review_pending = db.query(UnresolvedEvent).count()
    dead_letters = db.query(DeadLetter).count()
    events_ingested = events_processed + review_pending + dead_letters
    preservation_success = events_ingested
    integrity_failures = 0

    return {
        "events_ingested": events_ingested,
        "events_normalized": events_normalized,
        "events_processed": events_processed,
        "fast_events": fast_events,
        "adaptive_events": adaptive_events,
        "review_pending": review_pending,
        "dead_letters": dead_letters,
        "preservation_success": preservation_success,
        "integrity_failures": integrity_failures
    }

@app.get("/api/v1/system/health")
def get_system_health(db: Session = Depends(get_db)):
    # Postgres
    try:
        db.execute(text("SELECT 1"))
        postgres_status = "healthy"
    except Exception:
        postgres_status = "down"

    # Redis
    try:
        r = redis_lib.Redis.from_url(settings.REDIS_URI, socket_connect_timeout=2)
        r.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "down"

    # OpenSearch
    try:
        os_client = get_opensearch_client()
        if os_client.ping():
            opensearch_status = "healthy"
        else:
            opensearch_status = "down"
    except Exception:
        opensearch_status = "down"

    overall = "healthy"
    if any(s != "healthy" for s in [postgres_status, redis_status, opensearch_status]):
        overall = "degraded"

    return {
        "status": overall,
        "components": {
            "postgres": postgres_status,
            "redis": redis_status,
            "opensearch": opensearch_status,
        }
    }

# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Serve Frontend and SPA Fallback
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dir):
    logger.info(f"Serving frontend from {frontend_dir}")
    # Mount assets so we don't catch them in the SPA route
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")
    
    from fastapi.responses import FileResponse
    @app.get("/{catchall:path}")
    def serve_react_app(catchall: str):
        # Serve index.html for all non-api routes
        if not catchall.startswith("api/"):
            index_path = os.path.join(frontend_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
else:
    logger.warning("Frontend build not found, serving API only.")

# trigger reload
