from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.domain import Source, OnboardingSession, Mapping
import pytest
import uuid
import datetime
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_syslog_servers():
    with patch("app.main.start_syslog_servers", return_value=(None, None)):
        yield

@pytest.fixture(scope="module")
def db_session(request):
    from conftest import is_postgres_available
    if not is_postgres_available():
        pytest.skip("PostgreSQL infrastructure is unavailable")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.postgres
def test_upload_sample(db_session, client):
    # Setup test data
    source_id = "SRC-TEST-001"
    source = Source(
        source_id=source_id,
        name="Test Source",
        transport="http"
    )
    db_session.add(source)
    
    session_id = str(uuid.uuid4())
    session = OnboardingSession(
        id=session_id,
        source_id=source_id,
        status="STARTED",
        current_stage="SOURCE_SELECTION",
        started_at=datetime.datetime.utcnow()
    )
    db_session.add(session)
    db_session.commit()
    
    # Upload sample
    sample_content = b"user=admin action=login ip=10.0.0.1 status=success"
    response = client.post(
        f"/onboarding/{session_id}/sample",
        files={"file": ("sample.log", sample_content, "text/plain")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["processing_path"] in ["fast", "adaptive"]
    assert "template_id" in data
