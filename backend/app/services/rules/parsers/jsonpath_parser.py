import json
from typing import Any

from .base import BaseParser, ParserError


class JsonPathParser(BaseParser):
    def __init__(self, parser_def: dict[str, Any], field_mappings: dict[str, str]):
        super().__init__(parser_def, field_mappings)
        # Attempt to import jsonpath-ng, but fallback to simple dict traversal if unavailable
        try:
            from jsonpath_ng import parse
            self._jp_parse = parse
            self._paths = {k: parse(v) for k, v in self.parser_def.get("paths", {}).items()}
            self._use_jsonpath_ng = True
        except ImportError:
            self._use_jsonpath_ng = False
            self._paths = self.parser_def.get("paths", {})

    def parse(self, raw_event: str) -> dict[str, Any]:
        try:
            data = json.loads(raw_event)
        except json.JSONDecodeError:
            raise ParserError("Event is not valid JSON")
            
        result = {}
        for extract_key, canonical_field in self.field_mappings.items():
            path = self._paths.get(extract_key)
            if not path:
                continue
                
            if self._use_jsonpath_ng:
                matches = path.find(data)
                if matches:
                    result[canonical_field] = matches[0].value
            else:
                # Simple fallback for standard keys
                if path in data:
                    result[canonical_field] = data[path]
                    
        return result
