"""
T8 acceptance test: test gateway crash on file_id.
"""
import pytest
from sqlalchemy.orm import Session
from app.services.ingestion.gateway import process_ingestion

@pytest.mark.asyncio
async def test_gateway_process_ingestion_no_file_id_crash():
    from app.core.database import SessionLocal
    db_session = SessionLocal()
    try:
        # Setup source
        from app.models.domain import Source
        source = db_session.query(Source).filter(Source.source_id == "SRC-GATEWAY-TEST").first()
        if not source:
            source = Source(source_id="SRC-GATEWAY-TEST", name="Gateway Test Source", vendor="pytest")
            db_session.add(source)
            db_session.commit()
    
        # Call process_ingestion, it shouldn't crash
        trace_id = await process_ingestion(
            db=db_session,
            source_id="SRC-GATEWAY-TEST",
            payload=b"test payload",
            transport="pytest",
        )
        assert trace_id is not None
    finally:
        db_session.close()
