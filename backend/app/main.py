import logging
import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine

from app.api.sources import router as sources_router
from app.api.onboarding import router as onboarding_router
from app.api.rules import router as rules_router
from app.api.events import router as events_router
from app.api.jobs import router as jobs_router
from app.api.sessions import router as sessions_router
from app.api.api_keys import router as api_keys_router

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

@app.on_event("startup")
async def startup_event():
    logger.info("Starting ULPF API Server...")

# API Routers
API = "/api/v1"
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
def get_stats_overview():
    return {
        "total_sources": 0,
        "active_parsers": 0,
        "events_processed": 0,
        "throughput_eps": 0
    }

@app.get("/api/v1/system/health")
def get_system_health():
    return {
        "status": "healthy",
        "components": {
            "postgres": "up",
            "redis": "up",
            "opensearch": "up"
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
