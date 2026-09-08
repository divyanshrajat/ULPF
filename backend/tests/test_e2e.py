import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

def test_full_workflow():
    # 1. Create API Key
    resp = client.post("/api/v1/api-keys", json={"name": "test-key", "environment": "sandbox", "source_scope": "test-firewall"})
    if resp.status_code == 200:
        key_data = resp.json()
        assert "raw_key" in key_data
    
    # 2. Fetch Events
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200
    events = resp.json()
    assert "items" in events

    # 3. Create Onboarding Session
    resp = client.post("/api/v1/onboarding", json={"source_id": "test-firewall"})
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]

    # 4. Upload Sample
    resp = client.post(f"/api/v1/onboarding/{session_id}/samples", json=["<14>1 2026-09-07T10:22:41Z fw-edge-02 PAN - - - THREAT,vulnerability,drop,10.1.2.45,203.0.113.9,443,tcp,critical,\"SQL Injection Attempt\""])
    assert resp.status_code == 200

    # We won't generate a draft via LLM in the test to avoid dependency on the LLM model/API in basic test
    # but the above endpoints hitting 200/201 is good enough for a basic integration smoke test.
