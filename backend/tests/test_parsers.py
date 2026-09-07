import pytest
from app.services.extraction.deterministic import parser_registry

def test_parse_cef():
    payload = b"CEF:0|VendorX|FirewallX|1.0|100|Blocked Connection|8|src=10.0.0.1 dst=10.0.0.2 spt=443"
    parser = parser_registry.get_parser("cef")
    res = parser(payload)
    assert res["cef_version"] == "0"
    assert res["device_vendor"] == "VendorX"
    assert res["device_product"] == "FirewallX"
    assert res["device_version"] == "1.0"
    assert res["signature_id"] == "100"
    assert res["name"] == "Blocked Connection"
    assert res["severity"] == "8"
    assert res["src"] == "10.0.0.1"
    assert res["dst"] == "10.0.0.2"
    assert res["spt"] == "443"

def test_parse_leef():
    payload = b"LEEF:1.0|VendorY|ProductY|1.0|EventID1|src=10.0.0.1\tdst=10.0.0.2"
    parser = parser_registry.get_parser("leef")
    res = parser(payload)
    assert res["leef_version"] == "1.0"
    assert res["device_vendor"] == "VendorY"
    assert res["device_product"] == "ProductY"
    assert res["event_id"] == "EventID1"
    assert res["src"] == "10.0.0.1"
    assert res["dst"] == "10.0.0.2"

def test_parse_syslog_5424():
    payload = b"<165>1 2026-08-24T12:34:56.123Z mymachine.example.com evntslog - ID47 [exampleSDID@32473 iut=\"3\" eventSource=\"Application\" eventID=\"1011\"] BOMmy message"
    parser = parser_registry.get_parser("syslog_5424")
    res = parser(payload)
    assert res["syslog.priority"] == "165"
    assert res["syslog.version"] == "1"
    assert res["syslog.timestamp"] == "2026-08-24T12:34:56.123Z"
    assert res["syslog.hostname"] == "mymachine.example.com"
    assert res["syslog.message"] == "BOMmy message"

def test_parse_xml():
    payload = b"<event><host>fw01</host><action>deny</action><severity>8</severity><network><src_ip>10.0.0.1</src_ip></network></event>"
    parser = parser_registry.get_parser("xml")
    res = parser(payload)
    assert res["host"] == "fw01"
    assert res["action"] == "deny"
    assert res["severity"] == "8"
    assert res["network.src_ip"] == "10.0.0.1"

def test_parse_csv():
    payload = b'header1,header2,header3\nval1,"val 2",val3'
    parser = parser_registry.get_parser("csv")
    res = parser(payload)
    assert res["header1"] == "val1"
    assert res["header2"] == "val 2"
    assert res["header3"] == "val3"

def test_parse_tsv():
    payload = b'header1\theader2\theader3\nval1\tval 2\tval3'
    parser = parser_registry.get_parser("tsv")
    res = parser(payload)
    assert res["header1"] == "val1"
    assert res["header2"] == "val 2"
    assert res["header3"] == "val3"

def test_classifier_parser_consistency():
    from app.services.detection.classifier import classify_format
    
    # Just checking some known payloads
    json_payload = b'{"key": "value"}'
    detection = classify_format(json_payload)
    assert detection.format_name == "json"
    assert parser_registry.get_parser(detection.format_name) is not None

    csv_payload = b'h1,h2\nv1,v2'
    detection = classify_format(csv_payload)
    if detection.confidence >= 0.9:
        assert parser_registry.get_parser(detection.format_name) is not None
