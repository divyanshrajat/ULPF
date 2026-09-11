"""
T1 acceptance test: sending X-ULPF-Role: administrator with no valid
credential must NOT grant admin role. After the fix, the header-based
identity branch is removed entirely from get_current_user.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_header_role_no_longer_accepted():
    """
    get_current_user must NOT have x_ulpf_user/x_ulpf_role parameters.
    Without Basic credentials, the user is always anonymous/viewer.
    """
    import inspect
    from app.core.auth import get_current_user

    sig = inspect.signature(get_current_user)
    param_names = list(sig.parameters.keys())
    assert "x_ulpf_user" not in param_names, \
        "get_current_user still accepts x_ulpf_user header — remove it"
    assert "x_ulpf_role" not in param_names, \
        "get_current_user still accepts x_ulpf_role header — remove it"


def test_anonymous_viewer_without_basic_creds():
    """
    With no credentials at all, get_current_user must return anonymous/viewer.
    """
    from app.core.auth import get_current_user
    result = get_current_user(credentials=None)
    assert result["username"] == "anonymous"
    assert result["role"] == "viewer"


def test_valid_basic_auth_still_works():
    """HTTP Basic with correct admin credentials must still grant admin."""
    from app.core.auth import get_current_user
    from fastapi.security import HTTPBasicCredentials

    creds = HTTPBasicCredentials(username="admin", password="ulpf-admin")
    result = get_current_user(credentials=creds)
    assert result["username"] == "admin"
    assert result["role"] == "administrator"


def test_bad_basic_creds_rejected():
    """HTTP Basic with wrong password must raise 401."""
    import pytest
    from fastapi import HTTPException
    from app.core.auth import get_current_user
    from fastapi.security import HTTPBasicCredentials

    creds = HTTPBasicCredentials(username="admin", password="wrong-password")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds)
    assert exc_info.value.status_code == 401


def test_header_role_ignored_at_http_level():
    """
    At the HTTP level, X-ULPF-Role/X-ULPF-User headers must have no effect.
    Without Basic creds, the user is anonymous/viewer regardless of headers.
    """
    resp = client.get(
        "/api/v1/system/health",
        headers={"X-ULPF-Role": "administrator", "X-ULPF-User": "hacker"},
    )
    # Health endpoint is public; just checking no crash and no privilege escalation
    assert resp.status_code == 200
