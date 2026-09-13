import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, SessionLocal
from app.models.domain import User, OnboardingSession, Source, RuleVersion, Rule, UnresolvedEvent
import uuid
import json
from datetime import datetime
from app.core.auth import get_password_hash

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def admin_token(db_session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=f"admin_{user_id}",
        password_hash=get_password_hash("password123"),
        role="administrator",
        tenant_id="default"
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post("/api/v1/auth/login", data={"username": user.username, "password": "password123"})
    return response.json()["access_token"]

@pytest.fixture
def viewer_token(db_session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=f"viewer_{user_id}",
        password_hash=get_password_hash("password123"),
        role="viewer",
        tenant_id="default"
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post("/api/v1/auth/login", data={"username": user.username, "password": "password123"})
    return response.json()["access_token"]

def test_auth_consistency_mutating_endpoints():
    # Anonymous should be rejected on create_source
    response = client.post("/api/v1/sources", json={"name": "test"})
    assert response.status_code == 401

def test_signup_password_policy():
    # Weak password
    response = client.post("/api/v1/auth/signup", json={"username": "testuser", "password": "123"})
    assert response.status_code == 422 # Pydantic validation error

    # Valid password
    username = f"testuser_{uuid.uuid4()}"
    response = client.post("/api/v1/auth/signup", json={"username": username, "password": "strongpassword123"})
    assert response.status_code == 200

def test_approve_rule_regression(db_session, admin_token):
    # Setup test data
    source_id = f"SRC-TEST-{uuid.uuid4().hex[:6]}"
    source = Source(source_id=source_id, tenant_id="default", name="Test", vendor="Test", status="active", created_at=datetime.utcnow())
    db_session.add(source)
    
    session_id = str(uuid.uuid4())
    fingerprint = f"fp_{uuid.uuid4()}"
    obs = OnboardingSession(id=session_id, source_id=source_id, status="VALIDATION_PASSED", fingerprint=fingerprint)
    db_session.add(obs)
    
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name="Test Rule", description="Test", created_at=datetime.utcnow())
    db_session.add(rule)
    
    rv_id = str(uuid.uuid4())
    rv = RuleVersion(id=rv_id, rule_id=rule_id, version=1, status="PENDING_REVIEW", 
                    parser_type="regex", parser_definition={"engine": "re2", "pattern": ".*"}, 
                    field_mappings={}, required_fields=[], type_constraints={}, target_schema="ocsf", schema_version="1.0",
                    rule_hash="fake-hash-1", created_at=datetime.utcnow())
    db_session.add(rv)
    
    # Add unresolved event
    ev_id = str(uuid.uuid4())
    unresolved = UnresolvedEvent(id=ev_id, trace_id=ev_id, fingerprint=fingerprint)
    db_session.add(unresolved)
    
    db_session.commit()
    
    # Call approve_rule
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(f"/api/v1/onboarding/{session_id}/approve", json={"rule_version_id": rv_id, "comments": "ok"}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    
    # Verify rule is active
    db_session.refresh(rv)
    assert rv.status == "ACTIVE"

def test_approve_rule_zero_backlog(db_session, admin_token):
    # Setup test data without unresolved events
    source_id = f"SRC-TEST-{uuid.uuid4().hex[:6]}"
    source = Source(source_id=source_id, tenant_id="default", name="Test2", vendor="Test", status="active", created_at=datetime.utcnow())
    db_session.add(source)
    
    session_id = str(uuid.uuid4())
    fingerprint = f"fp_{uuid.uuid4()}"
    obs = OnboardingSession(id=session_id, source_id=source_id, status="VALIDATION_PASSED", fingerprint=fingerprint)
    db_session.add(obs)
    
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name="Test Rule 2", description="Test", created_at=datetime.utcnow())
    db_session.add(rule)
    
    rv_id = str(uuid.uuid4())
    rv = RuleVersion(id=rv_id, rule_id=rule_id, version=1, status="PENDING_REVIEW", 
                    parser_type="regex", parser_definition={"engine": "re2", "pattern": ".*"}, 
                    field_mappings={}, required_fields=[], type_constraints={}, target_schema="ocsf", schema_version="1.0",
                    rule_hash="fake-hash-2", created_at=datetime.utcnow())
    db_session.add(rv)
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(f"/api/v1/onboarding/{session_id}/approve", json={"rule_version_id": rv_id, "comments": "ok"}, headers=headers)
    
    assert response.status_code == 200
    
    db_session.refresh(rv)
    assert rv.status == "ACTIVE"
