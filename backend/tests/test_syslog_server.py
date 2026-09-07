import pytest
from app.services.ingestion.syslog_server import resolve_source
from app.models.domain import Source

class MockQuery:
    def __init__(self, sources):
        self.sources = sources
    def filter(self, condition):
        # condition is a BinaryExpression. We hack it to extract the peer_ip.
        peer_ip = condition.right.value
        self.result = [s for s in self.sources if s.namespace == peer_ip]
        return self
    def first(self):
        return self.result[0] if self.result else None

class MockDB:
    def __init__(self):
        self.sources = [
            Source(source_id="SRC-KNOWN", name="Known Source", namespace="192.168.1.100")
        ]
    def query(self, model):
        return MockQuery(self.sources)

def test_resolve_source_known():
    db = MockDB()
    source_id = resolve_source(db, "192.168.1.100")
    assert source_id == "SRC-KNOWN"

def test_resolve_source_unknown():
    db = MockDB()
    source_id = resolve_source(db, "10.0.0.99")
    assert source_id == "unknown-syslog-source"
