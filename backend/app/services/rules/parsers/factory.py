from typing import Any

from .base import BaseParser
from .jsonpath_parser import JsonPathParser
from .regex_parser import RegexParser
from .cef_parser import CEFParser
from .leef_parser import LEEFParser
from .kv_parser import KeyValueParser
from .xml_parser import XMLParser

from functools import lru_cache
from threading import Lock

_parser_cache = {}
_cache_lock = Lock()
MAX_CACHE_SIZE = 1000

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

    @staticmethod
    def get_cached_parser(rule_version_id: str, parser_type: str, parser_def: dict[str, Any], field_mappings: dict[str, str]) -> BaseParser:
        with _cache_lock:
            if rule_version_id in _parser_cache:
                return _parser_cache[rule_version_id]
            
            parser = ParserFactory.create(parser_type, parser_def, field_mappings)
            if len(_parser_cache) >= MAX_CACHE_SIZE:
                # simple eviction: remove an arbitrary item
                _parser_cache.pop(next(iter(_parser_cache)))
            _parser_cache[rule_version_id] = parser
            return parser

