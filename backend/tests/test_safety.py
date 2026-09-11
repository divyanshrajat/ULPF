"""
T7 acceptance test: Structural and forbidden-content validation on LLM rule output.
"""
import pytest
from app.services.rules.safety import validate_rule_definition

def test_validate_rule_definition_safe():
    definition = '''
def parse(log_line):
    parts = log_line.split(" ")
    return {"ip": parts[0]}
'''
    assert validate_rule_definition(definition) is True

def test_validate_rule_definition_unsafe_eval():
    definition = '''
def parse(log_line):
    return eval(log_line)
'''
    with pytest.raises(ValueError, match="Forbidden keyword 'eval' detected in rule definition."):
        validate_rule_definition(definition)

def test_validate_rule_definition_unsafe_import():
    definition = '''
import os
def parse(log_line):
    os.system("rm -rf /")
'''
    with pytest.raises(ValueError, match="Forbidden keyword 'import os' detected in rule definition."):
        # Depending on implementation, match can be generic
        validate_rule_definition(definition)

def test_validate_rule_definition_unsafe_exec():
    definition = '''
def parse(log_line):
    exec("print('hacked')")
'''
    with pytest.raises(ValueError, match="Forbidden"):
        validate_rule_definition(definition)
