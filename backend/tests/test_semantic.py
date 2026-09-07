import pytest
from app.services.mapping.semantic import semantic_mapper
from app.schemas.domain import CandidateField

class MockQuery:
    def filter(self, *args, **kwargs):
        return self
    def all(self):
        return []

class MockDB:
    def query(self, *args, **kwargs):
        return MockQuery()

def get_top_target(field_key):
    candidate = CandidateField(field_key=field_key, inferred_type="text")
    proposals = semantic_mapper.propose_mappings(MockDB(), "src1", "tpl1", candidate, "dummy pattern")
    if proposals:
        return proposals[0].target_field
    return None

def test_action_alias():
    assert get_top_target("action") == "event.action"
    assert get_top_target("ACT") == "event.action"

def test_message_alias():
    assert get_top_target("message") == "event.message"
    assert get_top_target("MSG") == "event.message"

def test_host_alias():
    assert get_top_target("host") == "device.hostname"
    assert get_top_target("HOSTNAME") == "device.hostname"

def test_vendor_alias():
    assert get_top_target("vendor") == "metadata.product.vendor"

def test_product_alias():
    assert get_top_target("product") == "metadata.product.name"

def test_whitespace_and_case():
    assert get_top_target("  AcTiOn  ".strip()) == "event.action"

def test_unknown_alias():
    candidate = CandidateField(field_key="totally_unknown_field_xyz", inferred_type="text")
    proposals = semantic_mapper.propose_mappings(MockDB(), "src1", "tpl1", candidate, "dummy pattern")
    assert proposals[0].confidence < 0.90
