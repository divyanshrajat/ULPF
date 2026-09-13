from app.services.normalization.engine import normalize_action

def test_normalize_action_known_aliases():
    assert normalize_action("permit") == "allow"
    assert normalize_action("pass") == "allow"
    assert normalize_action("accept") == "allow"
    
    assert normalize_action("drop") == "deny"
    assert normalize_action("block") == "deny"
    assert normalize_action("reject") == "deny"

def test_normalize_action_preserves_case():
    assert normalize_action("ConsoleLogin") == "ConsoleLogin"
    assert normalize_action("AssumeRole") == "AssumeRole"
    assert normalize_action("PutObject") == "PutObject"
    assert normalize_action("GetObject") == "GetObject"
    assert normalize_action("MyCustomAction") == "MyCustomAction"

def test_normalize_action_preserves_already_normalized():
    assert normalize_action("allow") == "allow"
    assert normalize_action("deny") == "deny"

def test_normalize_action_uppercase_aliases():
    assert normalize_action("PERMIT") == "allow"
    assert normalize_action("BLOCK") == "deny"
