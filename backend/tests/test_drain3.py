import pytest
from app.services.discovery.drain3_miner import masking_instructions
import re

def mask_text(text: str) -> str:
    masked = text
    for mi in masking_instructions:
        masked = re.sub(mi.pattern, mi.mask_with, masked)
    return masked

def test_timestamp_masking():
    # ISO timestamp
    text1 = "Event at 2026-08-24T12:34:56Z occurred"
    assert mask_text(text1) == "Event at <TIME> occurred"

    # Timestamp with ms
    text2 = "Event at 2026-08-24 12:34:56.123 occurred"
    assert mask_text(text2) == "Event at <TIME> occurred"

    # Timestamp with timezone
    text3 = "Event at 2026-08-24T12:34:56+05:30 occurred"
    assert mask_text(text3) == "Event at <TIME> occurred"

def test_number_masking():
    text = "user=1234 process=5678"
    assert mask_text(text) == "user=<NUM> process=<NUM>"
    
    # Negative number
    text2 = "offset=-100"
    assert mask_text(text2) == "offset=<NUM>"
