"""
T2 acceptance test: API key verification on ingestion endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_jobs_without_api_key():
    resp = client.post("/api/v1/jobs?source_id=SRC-TEST-001", files={"file": ("test.txt", b"content")})
    assert resp.status_code == 401
    assert "Bearer" in resp.json()["detail"] or "Not authenticated" in resp.json()["detail"] or "Missing" in resp.json()["detail"]

def test_sessions_without_api_key():
    resp = client.post("/api/v1/sessions", json={"source_id": "SRC-TEST-001"})
    assert resp.status_code == 401

def test_session_events_without_api_key():
    resp = client.post("/api/v1/sessions/fake-session/events", json=["event1"])
    assert resp.status_code == 401

def test_invalid_api_key():
    resp = client.post("/api/v1/sessions", json={"source_id": "SRC-TEST-001"}, headers={"Authorization": "Bearer invalid-key"})
    assert resp.status_code == 401

# We would also test valid keys and scope, but that requires setting up a key in the DB.
# For now, just test the enforcement.
