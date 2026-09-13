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
    session_id: str | None = None
    job_id: str | None = None

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

class SourceContext(BaseModel):
    user: str | None = None
    ip: str | None = None
    hostname: str | None = None
    mac_address: str | None = None
    device_type: str | None = None

class NetworkContext(BaseModel):
    src_ip: str | None = None
    dst_ip: str | None = None
    src_port: int | None = None
    dst_port: int | None = None
    protocol: str | None = None
    bytes_in: int | None = None
    bytes_out: int | None = None

class SecurityContext(BaseModel):
    action: str | None = None
    severity: str | None = None
    threat_name: str | None = None
    category: str | None = None

class NormalizedEvent(BaseModel):
    event_id: str = ""
    event_time: str = ""
    ingest_time: str = ""
    source: SourceContext = SourceContext()
    network: NetworkContext = NetworkContext()
    security: SecurityContext = SecurityContext()
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
