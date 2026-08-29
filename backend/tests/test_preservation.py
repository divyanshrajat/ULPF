import pytest
import asyncio
from datetime import datetime
from app.services.preservation.vault import vault
import shutil
import os

@pytest.mark.asyncio
async def test_raw_byte_preservation():
    source_id = "test_src"
    trace_id = "test_trace_123"
    received_at = datetime.utcnow()
    
    # Original bytes with tricky characters
    original_bytes = b'{"timestamp": "2026-08-29", "msg": "test \\n \\r \\t chars", "val": 123}\n'
    
    # Write to vault
    digest, uri = await vault.write_event(trace_id, source_id, original_bytes, received_at)
    
    # Retrieve from vault
    retrieved_bytes = await vault.read_event(source_id, received_at, trace_id)
    
    # 1. Byte Comparison
    assert retrieved_bytes == original_bytes, "Retrieved bytes do not match original bytes exactly"
    
    # 2. SHA-256 Comparison
    assert vault.verify_digest(retrieved_bytes, digest), "Digest verification failed"
    
    # Cleanup
    shutil.rmtree(os.path.join(vault.vault_dir, source_id), ignore_errors=True)
