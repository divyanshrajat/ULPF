import ast

FORBIDDEN_KEYWORDS = {
    "eval", "exec", "os", "subprocess", "open", "__import__", "sys", "shutil", "socket", "requests", "urllib"
}

def validate_rule_definition(definition: str) -> bool:
    """
    Validates a python rule definition to ensure it doesn't contain forbidden operations.
    Uses AST parsing to detect forbidden function calls or imports.
    Raises ValueError if unsafe.
    """
    try:
        tree = ast.parse(definition)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python syntax in rule definition: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_KEYWORDS:
                    raise ValueError(f"Forbidden keyword 'import {alias.name}' detected in rule definition.")
        elif isinstance(node, ast.ImportFrom):
            if node.module in FORBIDDEN_KEYWORDS:
                raise ValueError(f"Forbidden keyword 'import {node.module}' detected in rule definition.")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_KEYWORDS:
                raise ValueError(f"Forbidden keyword '{node.func.id}' detected in rule definition.")
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id in FORBIDDEN_KEYWORDS:
                raise ValueError(f"Forbidden keyword '{node.func.value.id}' detected in rule definition.")
                
    return True
