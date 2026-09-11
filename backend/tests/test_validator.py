import pytest
from app.services.rules.validator import RuleValidator, ValidationError

def test_validate_required_fields():
    extracted = {"time": "2023-01-01", "ip": "1.2.3.4"}
    
    # Should pass
    RuleValidator.validate_extracted_fields(extracted, ["time"])
    
    # Should fail
    with pytest.raises(ValidationError, match="Missing required fields: \\['user'\\]"):
        RuleValidator.validate_extracted_fields(extracted, ["time", "user"])

def test_validate_type_constraints():
    extracted = {
        "event_time": "2023-01-01T12:00:00Z",
        "ip": "10.0.0.1",
        "port": "80",
        "is_active": "true"
    }
    constraints = {
        "event_time": "datetime",
        "ip": "ip",
        "port": "int",
        "is_active": "boolean"
    }
    
    # Should pass
    RuleValidator.validate_extracted_fields(extracted, [], constraints)
    
    # Should fail int
    with pytest.raises(ValidationError, match="does not match type constraint 'int'"):
        RuleValidator.validate_extracted_fields({"port": "abc"}, [], {"port": "int"})
        
    # Should fail ip
    with pytest.raises(ValidationError, match="does not match type constraint 'ip'"):
        RuleValidator.validate_extracted_fields({"ip": "999.999.999.999"}, [], {"ip": "ip"})
        
    # Should fail datetime
    with pytest.raises(ValidationError, match="does not match type constraint 'datetime'"):
        RuleValidator.validate_extracted_fields({"event_time": "not a date"}, [], {"event_time": "datetime"})
