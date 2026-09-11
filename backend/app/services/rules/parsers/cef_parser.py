import re
from typing import Any
from app.services.rules.parsers.base import BaseParser, ParserError

class CEFParser(BaseParser):
    def parse(self, raw_event: str) -> dict[str, Any]:
        if not raw_event.startswith("CEF:"):
            raise ParserError("Event does not start with CEF:")
            
        parts = re.split(r'(?<!\\)\|', raw_event)
        if len(parts) < 8:
            raise ParserError(f"Invalid CEF format, expected at least 8 pipe-separated fields, got {len(parts)}")
            
        # Parse standard header fields
        extracted = {
            "cef_version": parts[0].replace("CEF:", ""),
            "device_vendor": parts[1].replace(r'\|', '|'),
            "device_product": parts[2].replace(r'\|', '|'),
            "device_version": parts[3].replace(r'\|', '|'),
            "device_event_class_id": parts[4].replace(r'\|', '|'),
            "name": parts[5].replace(r'\|', '|'),
            "severity": parts[6].replace(r'\|', '|')
        }
        
        # Parse extensions
        extensions_str = "|".join(parts[7:])
        
        # Simple kv extraction for extensions: key=value
        # Keys are alphanumeric, values can contain spaces, terminated by the next key= or end of string.
        # This is a simplified regex for CEF extensions.
        ext_matches = re.finditer(r'([a-zA-Z0-9]+)=((?:[^=](?!\s+[a-zA-Z0-9]+=))*[^=\s])', extensions_str)
        for match in ext_matches:
            extracted[match.group(1)] = match.group(2).replace(r'\=', '=').replace(r'\\', '\\')
            
        # Map fields
        result = {}
        for source_field, target_field in self.field_mappings.items():
            if source_field in extracted:
                result[target_field] = extracted[source_field]
                
        return result
