import json
import re
import csv
import io
import xml.etree.ElementTree as ET
from typing import Dict, Any, Callable, Optional

def parse_json(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    return json.loads(text)

def parse_key_value(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    # Matches k=v, k="v", k='v'
    matches = re.findall(r'\b(\w+)\s*=\s*([\'"]?)([^\s\'"]+)\2', text)
    result = {}
    for k, _, v in matches:
        result[k] = v
    return result

def parse_delimited(payload: bytes, delimiter: str = '|') -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    parts = text.split(delimiter)
    result = {}
    for i, part in enumerate(parts):
        result[f"pos_{i+1}"] = part.strip()
    return result

def parse_syslog_3164(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    # Basic parsing for <PRIVAL>TIMESTAMP HOSTNAME MSG
    match = re.match(r'^<(\d{1,3})>([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)', text)
    if match:
        return {
            "syslog.priority": match.group(1),
            "syslog.timestamp": match.group(2),
            "syslog.hostname": match.group(3),
            "syslog.message": match.group(4)
        }
    return {"raw_message": text}

def parse_syslog_5424(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    # <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
    match = re.match(r'^<(\d{1,3})>(\d{1,3})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(-|(?:\[.*?\])+)(?:\s+(.*))?$', text)
    if match:
        res = {
            "syslog.priority": match.group(1),
            "syslog.version": match.group(2),
            "syslog.timestamp": match.group(3),
            "syslog.hostname": match.group(4),
            "syslog.app_name": match.group(5),
            "syslog.procid": match.group(6),
            "syslog.msgid": match.group(7),
            "syslog.structured_data": match.group(8),
        }
        if match.group(9):
            res["syslog.message"] = match.group(9)
        return res
    return {"raw_message": text}

def parse_cef(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    # CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
    match = re.match(r'^CEF:(\d+)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|(.*)', text)
    if match:
        res = {
            "cef_version": match.group(1),
            "device_vendor": match.group(2),
            "device_product": match.group(3),
            "device_version": match.group(4),
            "signature_id": match.group(5),
            "name": match.group(6),
            "severity": match.group(7)
        }
        ext_text = match.group(8)
        # Using simple kv extraction
        ext_matches = re.findall(r'\b([\w.]+)\s*=\s*([\'"]?)(.*?)(?=\s+[\w.]+\s*=|$)', ext_text)
        for k, _, v in ext_matches:
            res[k] = v
        return res
    return {"raw_message": text}

def parse_leef(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    # LEEF:Version|Vendor|Product|Version|EventID|key=value...
    match = re.match(r'^LEEF:(\d+\.\d+)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|(.*)', text)
    if match:
        res = {
            "leef_version": match.group(1),
            "device_vendor": match.group(2),
            "device_product": match.group(3),
            "device_version": match.group(4),
            "event_id": match.group(5),
        }
        ext_text = match.group(6)
        # Using simple kv extraction
        ext_matches = re.findall(r'\b([\w.]+)\s*=\s*([\'"]?)(.*?)(?=\s+[\w.]+\s*=|$)', ext_text)
        for k, _, v in ext_matches:
            res[k] = v
        return res
    return {"raw_message": text}

def parse_xml(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    try:
        parser = ET.XMLParser()
        root = ET.fromstring(text, parser=parser)
        
        def flatten(elem, prefix=""):
            d = {}
            for child in elem:
                key = f"{prefix}{child.tag}" if prefix else child.tag
                if len(child):
                    d.update(flatten(child, f"{key}."))
                elif child.text and child.text.strip():
                    d[key] = child.text.strip()
            return d
            
        res = flatten(root)
        if not res and root.text and root.text.strip():
            res[root.tag] = root.text.strip()
        return res
    except ET.ParseError:
        return {"raw_message": text}

def parse_csv(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    f = io.StringIO(text)
    reader = csv.reader(f)
    try:
        header = next(reader)
        row = next(reader, None)
        if row:
            res = {}
            for k, v in zip(header, row):
                res[k.strip()] = v.strip() if isinstance(v, str) else v
            return res
    except Exception:
        pass
    return {"raw_message": text}

def parse_tsv(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    f = io.StringIO(text)
    reader = csv.reader(f, delimiter='\t')
    try:
        header = next(reader)
        row = next(reader, None)
        if row:
            res = {}
            for k, v in zip(header, row):
                res[k.strip()] = v.strip() if isinstance(v, str) else v
            return res
    except Exception:
        pass
    return {"raw_message": text}


class ParserRegistry:
    def __init__(self):
        self._parsers: Dict[str, Callable[[bytes], Dict[str, Any]]] = {
            "json": parse_json,
            "key_value": parse_key_value,
            "delimited_pipe": parse_delimited,
            "syslog_3164": parse_syslog_3164,
            "syslog_5424": parse_syslog_5424,
            "cef": parse_cef,
            "leef": parse_leef,
            "xml": parse_xml,
            "csv": parse_csv,
            "tsv": parse_tsv,
        }
        
    def get_parser(self, format_name: str) -> Optional[Callable[[bytes], Dict[str, Any]]]:
        return self._parsers.get(format_name)

parser_registry = ParserRegistry()
