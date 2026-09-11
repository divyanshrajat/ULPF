import re
import shlex
from typing import Any
from app.services.rules.parsers.base import BaseParser, ParserError

class KeyValueParser(BaseParser):
    def parse(self, raw_event: str) -> dict[str, Any]:
        extracted = {}
        
        delimiter = self.parser_def.get("delimiter", " ")
        kv_separator = self.parser_def.get("kv_separator", "=")
        
        # We can use shlex if the delimiter is space and values might be quoted
        if delimiter == " " and kv_separator == "=":
            try:
                tokens = shlex.split(raw_event)
                for token in tokens:
                    if "=" in token:
                        k, v = token.split("=", 1)
                        extracted[k] = v
            except ValueError:
                # If shlex fails (e.g. unmatched quotes), fallback to simple split
                pairs = raw_event.split(delimiter)
                for pair in pairs:
                    if kv_separator in pair:
                        k, v = pair.split(kv_separator, 1)
                        extracted[k.strip()] = v.strip(' "\'')
        else:
            pairs = raw_event.split(delimiter)
            for pair in pairs:
                if kv_separator in pair:
                    k, v = pair.split(kv_separator, 1)
                    extracted[k.strip()] = v.strip(' "\'')
                    
        # Map fields
        result = {}
        for source_field, target_field in self.field_mappings.items():
            if source_field in extracted:
                result[target_field] = extracted[source_field]
                
        return result
