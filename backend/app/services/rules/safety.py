import json
import re

def validate_rule_definition(definition: str) -> bool:
    """
    Validates a rule definition (JSON string) to ensure it doesn't contain unsafe patterns.
    - Limits total length.
    - Ensures valid JSON.
    - Checks regex patterns for potential ReDoS (e.g., nested quantifiers).
    """
    if len(definition) > 100 * 1024:
        raise ValueError("Rule definition exceeds maximum size of 100KB.")
        
    try:
        rule_data = json.loads(definition)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in rule definition: {e}")
        
    # Recursively find all string values that might be regexes (heuristic)
    def check_regexes(data):
        if isinstance(data, dict):
            for v in data.values():
                check_regexes(v)
        elif isinstance(data, list):
            for item in data:
                check_regexes(item)
        elif isinstance(data, str):
            # Check for ReDoS patterns: nested quantifiers like (a+)+
            if re.search(r'\([^)]*[+*][^)]*\)[+*]', data) or re.search(r'\[[^\]]*[+*][^\]]*\][+*]', data):
                raise ValueError(f"Forbidden nested quantifier detected in pattern: {data[:50]}")
            # Ensure it compiles if it has regex characters
            if any(c in data for c in '*+?()[]'):
                try:
                    re.compile(data)
                except re.error as e:
                    pass # Not everything with *+? is a regex, ignore compile errors
    
    check_regexes(rule_data)
    return True
