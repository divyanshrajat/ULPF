import re
from typing import Any
from app.services.rules.parsers.base import BaseParser, ParserError

class LEEFParser(BaseParser):
    def parse(self, raw_event: str) -> dict[str, Any]:
        if not raw_event.startswith("LEEF:"):
            raise ParserError("Event does not start with LEEF:")
            
        parts = re.split(r'(?<!\\)\|', raw_event, maxsplit=6)
        if len(parts) < 5:
            raise ParserError(f"Invalid LEEF format, expected at least 5 pipe-separated fields, got {len(parts)}")
            
        version_str = parts[0].replace("LEEF:", "")
        
        extracted = {
            "leef_version": version_str,
            "device_vendor": parts[1].replace(r'\|', '|'),
            "device_product": parts[2].replace(r'\|', '|'),
            "device_version": parts[3].replace(r'\|', '|'),
            "device_event_class_id": parts[4].replace(r'\|', '|')
        }
        
        delimiter = "\t" # default LEEF 1.0 delimiter
        extensions_idx = 5
        
        if version_str == "2.0" and len(parts) > 5:
            # For 2.0, the 6th field is the delimiter
            delimiter = parts[5]
            if not delimiter:
                delimiter = "\t"
            extensions_idx = 6
            
            # Re-split with the correct maxsplit because we need all remaining text
            parts = re.split(r'(?<!\\)\|', raw_event, maxsplit=extensions_idx)
            
        if len(parts) > extensions_idx:
            extensions_str = parts[extensions_idx]
            
            # In LEEF, delimiter separates key=value pairs, but wait, 
            # if delimiter is \t, then it's key=value\tkey=value.
            # However, some vendors just use spaces. We can handle it generically.
            
            if delimiter == 'x09' or delimiter == '\\t':
                delimiter = '\t'
            elif delimiter == 'x20' or delimiter == '\\s':
                delimiter = ' '
                
            kv_pairs = extensions_str.split(delimiter)
            for pair in kv_pairs:
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    extracted[k.strip()] = v.strip()
                    
        # Map fields
        result = {}
        for source_field, target_field in self.field_mappings.items():
            if source_field in extracted:
                result[target_field] = extracted[source_field]
                
        return result
