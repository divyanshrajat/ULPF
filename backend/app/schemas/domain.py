from datetime import datetime
from typing import Any

from pydantic import BaseModel


class IngestRecord(BaseModel):
    trace_id: str
    source_id: str
    payload: bytes
    byte_length: int
    received_at: datetime
    transport: str
    peer: str | None = None
    encoding_hint: str | None = None

class CandidateField(BaseModel):
    field_key: str
    position: str | None = None
    inferred_type: str | None = None
    sample_values: list[str] = []

class MappingProposal(BaseModel):
    source_field: str
    target_field: str
    confidence: float
    decision: str # "auto_accepted", "human_approved", "extension_only"
    signals: dict[str, float] = {}
    transformation: str = "direct"

class NormalizedEvent(BaseModel):
    event_id: str = ""
    event_time: str = ""
    ingest_time: str = ""
    source: dict[str, Any] = {}
    network: dict[str, Any] = {}
    security: dict[str, Any] = {}
    normalization: dict[str, Any] = {}
    raw_reference: dict[str, Any] = {}
    processing: dict[str, Any] = {}
    unmapped_fields: dict[str, Any] = {}

class ProvenanceRecord(BaseModel):
    trace_id: str
    target_field: str
    source_field: str
    source_value: str | None = None
    transformation: str
    mapping_id: str | None = None
    mapping_version: int | None = None
    schema_version: str | None = None
    confidence: float | None = None
    decision: str
