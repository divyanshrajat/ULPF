"""
T47 — Digest tamper-detection test (depends on T28: verify_digest in vault.py).
  - Compute digest for a known payload
  - vault.verify_digest(payload, digest) == True
  - Corrupt one byte
  - vault.verify_digest(corrupted, digest) == False
"""
import hashlib
import uuid
import pytest

from app.services.preservation.vault import vault


def test_verify_digest_passes_for_original_bytes():
    payload = b"This is a raw log event for digest verification."
    digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    assert vault.verify_digest(payload, digest) is True


def test_verify_digest_fails_after_single_byte_flip():
    payload = b"Raw event that will be tampered with."
    digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"

    corrupted = bytearray(payload)
    corrupted[0] ^= 0xFF  # flip one bit
    assert vault.verify_digest(bytes(corrupted), digest) is False, \
        "Single-byte corruption must fail digest verification."


def test_verify_digest_fails_for_wrong_digest():
    payload = b"Correct payload"
    wrong_digest = f"sha256:{'0' * 64}"
    assert vault.verify_digest(payload, wrong_digest) is False


def test_verify_digest_passes_for_empty_payload():
    payload = b""
    digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    assert vault.verify_digest(payload, digest) is True


def test_verify_digest_truncated_hash_fails():
    payload = b"Some event bytes."
    real_digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    # Shorten the hash
    truncated = real_digest[:20]
    assert vault.verify_digest(payload, truncated) is False
