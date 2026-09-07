import pytest
from app.services.discovery.drain3_miner import drain3_manager, masking_instructions
from app.services.discovery.extraction_service import discover_and_extract
from app.core.database import SessionLocal
from app.models.domain import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

def test_timestamp_only():
    log = "2026-09-07T12:34:56Z connection established"
    result = drain3_manager.mine("test_src", log)
    template, params = drain3_manager.extract("test_src", log)
    assert template is not None
    assert "re.error" not in str(template)

def test_timestamp_and_numeric():
    log = "2026-09-07T12:34:56Z connection established code=200"
    result = drain3_manager.mine("test_src_num", log)
    template, params = drain3_manager.extract("test_src_num", log)
    assert template is not None
    assert "<TIME>" in template
    assert "<NUM>" in template

def test_timestamp_multiple_masks():
    log = "2026-09-07T12:34:56Z src=10.10.10.15 port=443 pid=1234 action=ALLOW"
    result = drain3_manager.mine("test_src_multi", log)
    template, params = drain3_manager.extract("test_src_multi", log)
    assert template is not None
    assert "<TIME>" in template
    assert "<IP>" in template
    assert "<NUM>" in template
    # Verify timestamp wasn't split up
    assert "<NUM>-<NUM>" not in template

def test_discover_and_extract_flagship(db_session):
    log = b"<14>1 2026-08-31T10:15:22.123Z fw-tokyo-01 CEF:0|Cisco|ASA|9.0|100|ACCEPT|1|src=192.168.1.100 dst=10.0.0.5 spt=51234 dpt=443 proto=TCP act=permit"
    template, candidates = discover_and_extract(db_session, "fw-tokyo-01", log)
    assert template is not None
    assert template.pattern is not None
    assert "<TIME>" in template.pattern
