from abc import ABC, abstractmethod
from typing import Any


class ParserError(Exception):
    pass

class BaseParser(ABC):
    def __init__(self, parser_def: dict[str, Any], field_mappings: dict[str, str]):
        self.parser_def = parser_def
        self.field_mappings = field_mappings

    @abstractmethod
    def parse(self, raw_event: str) -> dict[str, Any]:
        """
        Parses the raw event and returns a dictionary of extracted fields mapped to their canonical names.
        """
