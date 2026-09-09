from typing import Any

from pydantic import BaseModel


class DetectedFormat(BaseModel):
    format_name: str
    confidence: float
    reason: str
    parsed_data: dict[str, Any] | None = None # If the parser was invoked
