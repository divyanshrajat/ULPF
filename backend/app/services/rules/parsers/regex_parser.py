import re
try:
    import re2
    HAS_RE2 = True
except ImportError:
    HAS_RE2 = False

from typing import Any

from .base import BaseParser, ParserError


class RegexParser(BaseParser):
    def __init__(self, parser_def: dict[str, Any], field_mappings: dict[str, str]):
        super().__init__(parser_def, field_mappings)
        pattern = self.parser_def.get("pattern")
        if not pattern:
            raise ParserError("Regex parser requires a 'pattern' definition")
        try:
            if HAS_RE2:
                self.regex = re2.compile(pattern)
            else:
                self.regex = re.compile(pattern)
        except Exception as e:
            raise ParserError(f"Invalid regex pattern: {e}")

    def parse(self, raw_event: str) -> dict[str, Any]:
        match = self.regex.search(raw_event)
        if not match:
            raise ParserError("Regex did not match the event")
            
        extracted = match.groupdict()
        result = {}
        
        # Also support capture groups by index if mapping looks like capture_1
        groups = match.groups()
        
        for capture_key, canonical_field in self.field_mappings.items():
            if capture_key in extracted:
                result[canonical_field] = extracted[capture_key]
            elif capture_key.startswith("capture_"):
                try:
                    idx = int(capture_key.split("_")[1]) - 1
                    if 0 <= idx < len(groups):
                        result[canonical_field] = groups[idx]
                except ValueError:
                    pass
        
        return result
