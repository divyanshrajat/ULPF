from typing import Dict, Any
from .base import BaseParser, ParserError
from .regex_parser import RegexParser
from .jsonpath_parser import JsonPathParser

class ParserFactory:
    @staticmethod
    def create(parser_type: str, parser_def: Dict[str, Any], field_mappings: Dict[str, str]) -> BaseParser:
        ptype = parser_type.lower()
        if ptype == "regex":
            return RegexParser(parser_def, field_mappings)
        elif ptype == "jsonpath":
            return JsonPathParser(parser_def, field_mappings)
        # Fallback/mock for others in MVP
        elif ptype in ["syslog", "cef", "leef", "keyvalue", "xml"]:
            # For MVP, we can treat them as specialized regex or custom logic. 
            # We'll use a generic fallback for now that just parses everything via Regex if they provide a pattern.
            return RegexParser(parser_def, field_mappings)
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")
