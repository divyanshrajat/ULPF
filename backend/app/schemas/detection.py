from pydantic import BaseModel
from typing import Optional, Dict, Any

class DetectedFormat(BaseModel):
    format_name: str
    confidence: float
    reason: str
    parsed_data: Optional[Dict[str, Any]] = None # If the parser was invoked
