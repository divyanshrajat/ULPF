"""
T43 — Malformed input tests:
  - Broken JSON routed to unresolved / dead-letter (jsonpath parser)
  - Invalid CEF escaping handled gracefully (no crash)
  - Invalid LEEF handled gracefully
  - Invalid XML parsed safely (no XXE)
  - Partial / empty lines skipped without crashing
"""
import pytest
from app.services.rules.parsers.factory import ParserFactory
from app.services.rules.parsers.base import ParserError


# ── regex parser ───────────────────────────────────────────────────────────────

def test_regex_parser_no_match_raises_parser_error():
    """A regex pattern that cannot match the input must raise ParserError."""
    parser = ParserFactory.create(
        "regex",
        # Pattern requires 'host port' at the start; input below does not match
        {"pattern": r"^(?P<host>\S+) (?P<port>\d+) (?P<msg>.+)$"},
        {"host": "src_host", "port": "src_port", "msg": "message"},
    )
    with pytest.raises(ParserError):
        # Only two tokens — cannot satisfy the three-group pattern
        parser.parse("malformed_no_match_line")


# ── JSON/JSONPath parser ───────────────────────────────────────────────────────

def test_jsonpath_parser_broken_json_raises_parser_error():
    parser = ParserFactory.create(
        "jsonpath",
        {},
        {"$.src_ip": "network.src_ip"},
    )
    with pytest.raises(ParserError):
        parser.parse("{not valid json:::}")


def test_jsonpath_parser_empty_string_raises_parser_error():
    parser = ParserFactory.create("jsonpath", {}, {})
    with pytest.raises(ParserError):
        parser.parse("")


# ── CEF parser ────────────────────────────────────────────────────────────────

def test_cef_parser_valid_line_parsed():
    parser = ParserFactory.create(
        "cef",
        {},
        {"src": "network.src_ip", "dst": "network.dst_ip"},
    )
    line = "CEF:0|Security|threatmanager|1.0|100|worm successfully stopped|10|src=10.0.0.1 dst=2.1.2.2"
    result = parser.parse(line)
    # The parser extracts src/dst from the extension section
    assert "src" in result or "network.src_ip" in result


def test_cef_parser_non_cef_line_raises_parser_error():
    parser = ParserFactory.create("cef", {}, {"src": "network.src_ip"})
    with pytest.raises(ParserError):
        parser.parse("not a cef line at all")


def test_cef_parser_truncated_header_raises_parser_error():
    parser = ParserFactory.create("cef", {}, {})
    with pytest.raises(ParserError):
        # Only 3 pipe-delimited fields instead of 7
        parser.parse("CEF:0|Security|threatmanager")


# ── LEEF parser ───────────────────────────────────────────────────────────────

def test_leef_parser_valid_line_parsed():
    parser = ParserFactory.create(
        "leef",
        {},
        {"src": "network.src_ip"},
    )
    line = "LEEF:1.0|Microsoft|MSExchange|4.0|15345|src=192.0.2.0\tproto=TCP\tdst=172.50.123.1"
    result = parser.parse(line)
    assert isinstance(result, dict)


def test_leef_parser_non_leef_line_raises_parser_error():
    parser = ParserFactory.create("leef", {}, {})
    with pytest.raises(ParserError):
        parser.parse("just a plain log line, not LEEF")


# ── KeyValue parser ────────────────────────────────────────────────────────────

def test_kv_parser_valid_pairs():
    parser = ParserFactory.create(
        "keyvalue",
        {"delimiter": " ", "kv_separator": "="},
        {"src_ip": "network.src_ip", "user": "actor.user"},
    )
    result = parser.parse("src_ip=10.0.0.1 user=alice action=login")
    # Parser applies field_mappings; output keys are the target (mapped) names
    assert result.get("network.src_ip") == "10.0.0.1"
    assert result.get("actor.user") == "alice"


def test_kv_parser_empty_string_returns_empty_dict():
    parser = ParserFactory.create("keyvalue", {}, {})
    result = parser.parse("   ")
    assert isinstance(result, dict)


# ── XML parser ─────────────────────────────────────────────────────────────────

def test_xml_parser_valid_xml_parsed():
    """XML parser uses slash-separated paths rooted at the root element."""
    parser = ParserFactory.create(
        "xml",
        {},
        # Paths use the actual XML tag structure with / separators
        {"Event/System/EventID": "event.id", "Event/System/Computer": "host.name"},
    )
    xml = "<Event><System><EventID>4624</EventID><Computer>WORKSTATION1</Computer></System></Event>"
    result = parser.parse(xml)
    assert result.get("event.id") == "4624"
    assert result.get("host.name") == "WORKSTATION1"


def test_xml_parser_malformed_xml_raises_parser_error():
    parser = ParserFactory.create("xml", {}, {})
    with pytest.raises(ParserError):
        parser.parse("<unclosed>")


def test_xml_parser_xxe_entity_blocked():
    """XXE external entity injection must not make a network call or read files."""
    parser = ParserFactory.create("xml", {}, {})
    xxe_payload = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        "<root>&xxe;</root>"
    )
    # Should either raise ParserError or return safely (no filesystem access)
    try:
        result = parser.parse(xxe_payload)
        combined = str(result)
        assert "root:x:" not in combined, "XXE payload leaked /etc/passwd content"
    except ParserError:
        pass  # explicit rejection is also acceptable
