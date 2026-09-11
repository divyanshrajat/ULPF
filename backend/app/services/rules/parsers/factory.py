from typing import Any

from .base import BaseParser
from .jsonpath_parser import JsonPathParser
from .regex_parser import RegexParser
from .cef_parser import CEFParser
from .leef_parser import LEEFParser
from .kv_parser import KeyValueParser
from .xml_parser import XMLParser

class ParserFactory:
    @staticmethod
    def create(parser_type: str, parser_def: dict[str, Any], field_mappings: dict[str, str]) -> BaseParser:
        ptype = parser_type.lower()
        if ptype == "regex":
            return RegexParser(parser_def, field_mappings)
        elif ptype == "jsonpath":
            return JsonPathParser(parser_def, field_mappings)
        elif ptype == "cef":
            return CEFParser(parser_def, field_mappings)
        elif ptype == "leef":
            return LEEFParser(parser_def, field_mappings)
        elif ptype == "keyvalue" or ptype == "kv":
            return KeyValueParser(parser_def, field_mappings)
        elif ptype == "xml":
            return XMLParser(parser_def, field_mappings)
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")
