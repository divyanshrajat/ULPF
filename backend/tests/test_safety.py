"""
T7 acceptance test: Structural and forbidden-content validation on LLM rule output.
"""
import pytest
import json
from app.services.rules.safety import validate_rule_definition

def test_validate_rule_definition_safe():
    definition = json.dumps({
        "parser_type": "regex",
        "parser_definition": {
            "pattern": "^(?P<ip>[0-9.]+)$"
        }
    })
    assert validate_rule_definition(definition) is True

def test_validate_rule_definition_unsafe_redos_1():
    definition = json.dumps({
        "parser_type": "regex",
        "parser_definition": {
            "pattern": "^(.*)*$"
        }
    })
    with pytest.raises(ValueError, match="Forbidden nested quantifier"):
        validate_rule_definition(definition)

def test_validate_rule_definition_unsafe_redos_2():
    definition = json.dumps({
        "parser_type": "regex",
        "parser_definition": {
            "pattern": "^(a+)+$"
        }
    })
    with pytest.raises(ValueError, match="Forbidden nested quantifier"):
        validate_rule_definition(definition)

def test_validate_rule_definition_unsafe_size():
    definition = "x" * (100 * 1024 + 1)
    with pytest.raises(ValueError, match="exceeds maximum size"):
        validate_rule_definition(definition)

