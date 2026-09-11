"""
T4 acceptance test: a rule that fails to parse produces a dead letter
with error_class == "ParserError", not "NameError".
"""
import asyncio
import uuid
from unittest.mock import MagicMock, patch

import pytest


def test_parser_error_not_name_error():
    """
    When ParserFactory.create().parse() raises ParserError in the fast path,
    the dead letter must record error_class='ParserError', never 'NameError'.
    """
    from app.services.rules.parsers.base import ParserError

    # Build a minimal EventRecord-like object
    record = MagicMock()
    record.trace_id = str(uuid.uuid4())
    record.source_id = "test-source"
    record.payload = b"some raw log line"
    record.byte_length = len(record.payload)

    # We need a fake DB session and fake rule version
    fake_rule_version = MagicMock()
    fake_rule_version.parser_type = "regex"
    fake_rule_version.parser_definition = {"pattern": "(?P<msg>.*)"}
    fake_rule_version.field_mappings = {"msg": "message"}
    fake_rule_version.required_fields = ["msg"]
    fake_rule_version.id = "rv-1"
    fake_rule_version.rule_id = "rule-1"
    fake_rule_version.version = 1
    fake_rule_version.rule_hash = "abc"
    fake_rule_version.schema_version = "1.0"

    dead_letters_created = []

    def mock_create_dead_letter(db, trace_id, source_id, stage, error):
        dead_letters_created.append({
            "trace_id": trace_id,
            "source_id": source_id,
            "stage": stage,
            "error_class": error.__class__.__name__,
        })

    # Patch the parser to raise ParserError
    def mock_parser_create(*args, **kwargs):
        parser = MagicMock()
        parser.parse.side_effect = ParserError("bad regex match")
        return parser

    with patch("app.workers.processor.SessionLocal") as mock_session_cls, \
         patch("app.workers.processor.generate_fingerprint", return_value="fp-abc"), \
         patch("app.workers.processor.find_active_rule_by_fingerprint", return_value=fake_rule_version), \
         patch("app.workers.processor.ParserFactory") as mock_factory, \
         patch("app.workers.processor._create_dead_letter", side_effect=mock_create_dead_letter), \
         patch("app.workers.processor.event_queue") as mock_queue:

        mock_factory.create = mock_parser_create
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        from app.workers.processor import process_event
        asyncio.run(process_event(record))

    # The key assertion: error_class must be ParserError, not NameError
    assert len(dead_letters_created) == 1, f"Expected 1 dead letter, got {len(dead_letters_created)}"
    assert dead_letters_created[0]["error_class"] == "ParserError", \
        f"Expected error_class='ParserError', got '{dead_letters_created[0]['error_class']}'"
