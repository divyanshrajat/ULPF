import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.domain import Rule, RuleVersion

def test_unique_active_rule_version():
    db = SessionLocal()
    
    # Create rule
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name="Test Rule", status="ACTIVE")
    db.add(rule)
    db.commit()
    
    # Create first ACTIVE version
    v1 = RuleVersion(
        id=str(uuid.uuid4()),
        rule_id=rule_id,
        version=1,
        parser_type="regex",
        parser_definition={"pattern": ".*"},
        field_mappings={},
        target_schema="ocsf",
        schema_version="1.0",
        rule_hash="hash1",
        status="ACTIVE"
    )
    db.add(v1)
    db.commit()
    
    # Create second ACTIVE version - SHOULD FAIL
    v2 = RuleVersion(
        id=str(uuid.uuid4()),
        rule_id=rule_id,
        version=2,
        parser_type="regex",
        parser_definition={"pattern": ".*"},
        field_mappings={},
        target_schema="ocsf",
        schema_version="1.0",
        rule_hash="hash2",
        status="ACTIVE"
    )
    db.add(v2)
    
    with pytest.raises(IntegrityError):
        db.commit()
        
    db.rollback()
    
    # But another DRAFT version should succeed
    v3 = RuleVersion(
        id=str(uuid.uuid4()),
        rule_id=rule_id,
        version=3,
        parser_type="regex",
        parser_definition={"pattern": ".*"},
        field_mappings={},
        target_schema="ocsf",
        schema_version="1.0",
        rule_hash="hash3",
        status="DRAFT"
    )
    db.add(v3)
    db.commit()
    
    # Clean up
    db.delete(v3)
    db.delete(v1)
    db.delete(rule)
    db.commit()
    db.close()
