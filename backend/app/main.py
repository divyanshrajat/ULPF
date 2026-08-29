from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models.domain import Base

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dist, "index.html"))
    
    # Catch-all for SPA routing (if any future routes are added)
    @app.middleware("http")
    async def spa_middleware(request, call_next):
        response = await call_next(request)
        if response.status_code == 404 and not request.url.path.startswith("/api/") and not request.url.path.startswith("/docs"):
            return FileResponse(os.path.join(frontend_dist, "index.html"))
        return response
else:
    @app.get("/")
    def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    return {"status": "HEALTHY"}

@app.get("/readiness")
def readiness_check():
    return {"status": "READY"}

# Include routers later
from app.api.endpoints import router as api_router
from app.api.onboarding import base_router as onboarding_router
from app.api.queries import router as query_router
from app.api.review import router as review_router
from app.services.ingestion.syslog_server import start_syslog_servers
from app.workers.processor import worker_loop
import asyncio

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(onboarding_router, prefix=settings.API_V1_STR)
app.include_router(query_router, prefix=settings.API_V1_STR)
app.include_router(review_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    # Initialize DB tables (MVP fallback for missing migrations)
    Base.metadata.create_all(bind=engine)
    
    # Start syslog servers
    app.state.syslog_udp, app.state.syslog_tcp = await start_syslog_servers()
    
    # Start worker loop
    app.state.worker_task = asyncio.create_task(worker_loop())

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, 'syslog_udp'):
        app.state.syslog_udp.close()
    if hasattr(app.state, 'syslog_tcp'):
        app.state.syslog_tcp.close()
        await app.state.syslog_tcp.wait_closed()

