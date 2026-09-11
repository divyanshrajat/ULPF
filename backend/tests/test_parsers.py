import pytest
from app.services.rules.parsers.factory import ParserFactory

def test_cef_parser():
    raw = "CEF:0|Security|threatmanager|1.0|100|worm successfully stopped|10|src=10.0.0.1 dst=2.1.2.2 spt=1232"
    parser = ParserFactory.create("cef", {}, {"src": "source_ip", "name": "event_name"})
    result = parser.parse(raw)
    assert result["source_ip"] == "10.0.0.1"
    assert result["event_name"] == "worm successfully stopped"

def test_leef_parser_1_0():
    raw = "LEEF:1.0|Microsoft|Exchange|2007 SP1|1544|src=10.50.100.33\tdst=2.1.2.2"
    parser = ParserFactory.create("leef", {}, {"src": "source_ip"})
    result = parser.parse(raw)
    assert result["source_ip"] == "10.50.100.33"

def test_leef_parser_2_0():
    raw = "LEEF:2.0|Vendor|Product|1.0|ID|^|src=10.0.0.1^dst=2.1.2.2"
    parser = ParserFactory.create("leef", {}, {"src": "source_ip", "dst": "dest_ip"})
    result = parser.parse(raw)
    assert result["source_ip"] == "10.0.0.1"
    assert result["dest_ip"] == "2.1.2.2"

def test_kv_parser():
    raw = 'a=1 b="hello world" c=3'
    parser = ParserFactory.create("keyvalue", {"delimiter": " ", "kv_separator": "="}, {"b": "msg"})
    result = parser.parse(raw)
    assert result["msg"] == "hello world"

def test_xml_parser():
    raw = "<Event><System><EventID>4624</EventID></System><EventData><Data Name='SubjectUserSid'>S-1-5-18</Data></EventData></Event>"
    parser = ParserFactory.create("xml", {}, {"Event/System/EventID": "event_id"})
    result = parser.parse(raw)
    assert result["event_id"] == "4624"

    # Testing relative fallback
    parser = ParserFactory.create("xml", {}, {"System/EventID": "event_id"})
    result = parser.parse(raw)
    assert result["event_id"] == "4624"
