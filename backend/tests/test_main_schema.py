import pytest
from app.models.domain import RuleVersion
from app.services.normalization.engine import normalization_engine
from app.services.rules.parsers.jsonpath_parser import JsonPathParser
from app.core.database import SessionLocal

def test_demo_cloudtrail_rule_schema():
    # Use the same parser definition as in main.py
    parser_def = {
        "paths": {
            "userIdentity.arn": "$.userIdentity.arn",
            "sourceIPAddress": "$.sourceIPAddress",
            "eventName": "$.eventName",
            "eventTime": "$.eventTime"
        }
    }
    
    # Use the corrected mappings from main.py
    mappings = {
        "userIdentity.arn": "source.user", 
        "sourceIPAddress": "source.ip",
        "eventName": "security.action",
        "eventTime": "event_time"
    }
    
    parser = JsonPathParser(parser_def, mappings)
    
    raw_event = '{"eventTime":"2026-09-07T09:58:03Z","eventSource":"iam.amazonaws.com","eventName":"ConsoleLogin","sourceIPAddress":"198.51.100.22","userIdentity":{"arn":"arn:aws:iam::4021:user/asha"}}'
    
    parsed_data = parser.parse(raw_event)
    
    assert "source.user" in parsed_data
    assert "source.ip" in parsed_data
    assert "security.action" in parsed_data
    assert "event_time" in parsed_data
    
    assert parsed_data["source.user"] == "arn:aws:iam::4021:user/asha"
    assert parsed_data["source.ip"] == "198.51.100.22"
    assert parsed_data["security.action"] == "ConsoleLogin"
    assert parsed_data["event_time"] == "2026-09-07T09:58:03Z"

    # Test normalization engine output
    db = SessionLocal()
    
    # Mock template_id
    template_id = "test-rule-v1"
    
    event_dict, prov_records = normalization_engine.normalize(
        db=db,
        parsed_data=parsed_data,
        source_id="cloudtrail",
        template_id=template_id,
        trace_id="test-trace-1",
        raw_ref={}
    )
    
    assert event_dict["source"]["user"] == "arn:aws:iam::4021:user/asha"
    assert event_dict["source"]["ip"] == "198.51.100.22"
    assert event_dict["security"]["action"] == "ConsoleLogin" # Action vocab might not transform if not matched, but it exists
    assert event_dict["event_time"] == "2026-09-07T09:58:03Z"
