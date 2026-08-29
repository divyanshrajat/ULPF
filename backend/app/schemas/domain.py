from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class IngestRecord(BaseModel):
    trace_id: str
    source_id: str
    payload: bytes
    byte_length: int
    received_at: datetime
    transport: str
    peer: Optional[str] = None
    encoding_hint: Optional[str] = None

class CandidateField(BaseModel):
    field_key: str
    position: Optional[str] = None
    inferred_type: Optional[str] = None
    sample_values: List[str] = []

class MappingProposal(BaseModel):
    source_field: str
    target_field: str
    confidence: float
    decision: str # "auto_accepted", "human_approved", "extension_only"
    signals: Dict[str, float] = {}
    transformation: str = "direct"

class NormalizedEvent(BaseModel):
    metadata: Dict[str, Any] = {}
    time: Dict[str, Any] = {}
    source: Dict[str, Any] = {}
    destination: Dict[str, Any] = {}
    network: Dict[str, Any] = {}
    event: Dict[str, Any] = {}
    device: Dict[str, Any] = {}
    observer: Dict[str, Any] = {}
    extensions: Dict[str, Any] = {}
    raw_ref: Dict[str, Any] = {}

class ProvenanceRecord(BaseModel):
    trace_id: str
    target_field: str
    source_field: str
    source_value: Optional[str] = None
    transformation: str
    mapping_id: Optional[str] = None
    mapping_version: Optional[int] = None
    schema_version: Optional[str] = None
    confidence: Optional[float] = None
    decision: str
