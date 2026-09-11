import pytest
from app.authoring.prompt import redact_secrets, build_prompt

def test_redact_secrets_bearer_token():
    sample = "User logged in with Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    redacted = redact_secrets(sample)
    assert "eyJhbGci" not in redacted
    assert "Authorization: Bearer [REDACTED]" in redacted

def test_redact_secrets_basic_auth():
    sample = "Authorization: Basic YWRtaW46cGFzc3dvcmQxMjM="
    redacted = redact_secrets(sample)
    assert "YWRtaW4" not in redacted
    assert "Authorization: Basic [REDACTED]" in redacted

def test_redact_secrets_password():
    sample = 'login attempt password="MySuperSecretPassword!" user=admin'
    redacted = redact_secrets(sample)
    assert "password=[REDACTED]" in redacted

def test_redact_secrets_aws_key():
    sample = "Got AWS request with key AKIAIOSFODNN7EXAMPLE for bucket"
    redacted = redact_secrets(sample)
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[AWS_ACCESS_KEY_REDACTED]" in redacted

def test_build_prompt_redacts_samples():
    samples = [
        "Normal log line",
        "Sensitive log line password=hidden"
    ]
    prompt = build_prompt(samples)
    assert "Normal log line" in prompt
    assert "password=[REDACTED]" in prompt
    assert "hidden" not in prompt
