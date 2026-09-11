import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.domain import Tenant, User, Source
import uuid
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_isolation_data():
    db = SessionLocal()
    
    tenant_a_id = f"tenant_a_{uuid.uuid4().hex[:8]}"
    tenant_b_id = f"tenant_b_{uuid.uuid4().hex[:8]}"
    
    tenant_a = Tenant(id=tenant_a_id, name="Acme Corp")
    tenant_b = Tenant(id=tenant_b_id, name="Globex Inc")
    db.add(tenant_a)
    db.add(tenant_b)
    
    user_a = User(
        id=str(uuid.uuid4()),
        username=f"alice_{uuid.uuid4().hex[:8]}",
        password_hash=pwd_context.hash("password"),
        role="administrator",
        tenant_id=tenant_a_id
    )
    user_b = User(
        id=str(uuid.uuid4()),
        username=f"bob_{uuid.uuid4().hex[:8]}",
        password_hash=pwd_context.hash("password"),
        role="administrator",
        tenant_id=tenant_b_id
    )
    db.add(user_a)
    db.add(user_b)
    
    source_a = Source(
        source_id=f"acme-syslog-{uuid.uuid4().hex[:8]}",
        name="Acme Syslog",
        tenant_id=tenant_a_id
    )
    db.add(source_a)
    db.commit()
    
    yield {
        "tenant_a_id": tenant_a_id,
        "tenant_b_id": tenant_b_id,
        "user_a_username": user_a.username,
        "user_b_username": user_b.username,
        "source_a_id": source_a.source_id
    }
    
    # Teardown
    db.delete(source_a)
    db.delete(user_a)
    db.delete(user_b)
    db.delete(tenant_a)
    db.delete(tenant_b)
    db.commit()
    db.close()


def test_tenant_isolation_sources(setup_isolation_data):
    data = setup_isolation_data
    
    # Alice should see the source
    resp_a = client.get("/api/v1/sources", auth=(data["user_a_username"], "password"))
    assert resp_a.status_code == 200
    sources_a = resp_a.json()
    assert any(s["source_id"] == data["source_a_id"] for s in sources_a)
    
    # Bob should NOT see the source
    resp_b = client.get("/api/v1/sources", auth=(data["user_b_username"], "password"))
    assert resp_b.status_code == 200
    sources_b = resp_b.json()
    assert not any(s["source_id"] == data["source_a_id"] for s in sources_b)
