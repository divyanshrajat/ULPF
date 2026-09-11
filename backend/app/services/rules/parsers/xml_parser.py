import xml.etree.ElementTree as ET
from typing import Any
from app.services.rules.parsers.base import BaseParser, ParserError

class XMLParser(BaseParser):
    def parse(self, raw_event: str) -> dict[str, Any]:
        try:
            # In Python 3.8+, standard ElementTree ignores external entities by default
            # making it generally safe against XXE.
            root = ET.fromstring(raw_event)
        except ET.ParseError as e:
            raise ParserError(f"Failed to parse XML: {e}")
            
        extracted = {}
        
        # Simple extraction: paths like "Event/System/EventID"
        def extract_paths(elem, current_path=""):
            # Add attributes
            for k, v in elem.attrib.items():
                attr_path = f"{current_path}/@{k}" if current_path else f"@{k}"
                extracted[attr_path] = v
                
            # Add text
            if elem.text and elem.text.strip():
                extracted[current_path] = elem.text.strip()
                
            # Recurse
            for child in elem:
                child_path = f"{current_path}/{child.tag}" if current_path else child.tag
                extract_paths(child, child_path)
                
        extract_paths(root, root.tag)
        
        # Map fields
        result = {}
        for source_field, target_field in self.field_mappings.items():
            if source_field in extracted:
                result[target_field] = extracted[source_field]
            else:
                # Try finding it relative to root if the user omitted root tag
                alt_path = f"{root.tag}/{source_field}"
                if alt_path in extracted:
                    result[target_field] = extracted[alt_path]
                
        return result
