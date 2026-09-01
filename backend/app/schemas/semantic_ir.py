"""
semantic_ir.py — Universal Log Pre-processing Framework Semantic Intermediate Representation (IR).

The ULPF Semantic IR is a schema-agnostic canonical model that captures normalized
security, network, web, identity, and system event semantics before serializing
to standard schemas like OCSF (v1.1.0) and ECS (v8.11).
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class SourceEndpoint:
    ip: Optional[str] = None
    port: Optional[int] = None
    hostname: Optional[str] = None
    user: Optional[str] = None
    mac: Optional[str] = None
    nat_ip: Optional[str] = None
    nat_port: Optional[int] = None
    domain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class DestinationEndpoint:
    ip: Optional[str] = None
    port: Optional[int] = None
    hostname: Optional[str] = None
    mac: Optional[str] = None
    nat_ip: Optional[str] = None
    nat_port: Optional[int] = None
    service_name: Optional[str] = None
    domain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class NetworkInfo:
    protocol: Optional[str] = None
    transport: Optional[str] = None
    direction: Optional[str] = None
    bytes: Optional[int] = None
    bytes_in: Optional[int] = None
    bytes_out: Optional[int] = None
    packets: Optional[int] = None
    packets_in: Optional[int] = None
    packets_out: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class HttpInfo:
    method: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    query: Optional[str] = None
    version: Optional[str] = None
    status_code: Optional[int] = None
    response_bytes: Optional[int] = None
    request_bytes: Optional[int] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class EventInfo:
    category: Optional[str] = None
    type: Optional[str] = None
    action: Optional[str] = None
    outcome: Optional[str] = None  # "allow", "deny", "success", "failure", "unknown"
    severity: Optional[str] = None
    severity_id: Optional[int] = None
    message: Optional[str] = None
    dataset: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class DeviceInfo:
    hostname: Optional[str] = None
    ip: Optional[str] = None
    type: Optional[str] = None
    vendor: Optional[str] = None
    product: Optional[str] = None
    os: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ObserverInfo:
    source_id: Optional[str] = None
    hostname: Optional[str] = None
    ip: Optional[str] = None
    vendor: Optional[str] = None
    product: Optional[str] = None
    transport: Optional[str] = None
    version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class UserInfo:
    name: Optional[str] = None
    domain: Optional[str] = None
    id: Optional[str] = None
    email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class RawReference:
    trace_id: str
    digest: str
    byte_length: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "digest": self.digest,
            "byte_length": self.byte_length,
        }


@dataclass
class ULPFSemanticIR:
    trace_id: str
    event_time_utc: Optional[str] = None
    event_time_original: Optional[str] = None
    source: SourceEndpoint = field(default_factory=SourceEndpoint)
    destination: DestinationEndpoint = field(default_factory=DestinationEndpoint)
    network: NetworkInfo = field(default_factory=NetworkInfo)
    http: HttpInfo = field(default_factory=HttpInfo)
    event: EventInfo = field(default_factory=EventInfo)
    device: DeviceInfo = field(default_factory=DeviceInfo)
    observer: ObserverInfo = field(default_factory=ObserverInfo)
    user: UserInfo = field(default_factory=UserInfo)
    extensions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    raw_ref: Optional[RawReference] = None
    mapping_version: Optional[int] = None
    processing_path: str = "adaptive"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "trace_id": self.trace_id,
                "schema_version": "ulpf-core-1.0",
                "mapping_version": self.mapping_version,
                "processing_path": self.processing_path,
            },
            "time": {
                k: v for k, v in {
                    "event_time_utc": self.event_time_utc,
                    "event_time_original": self.event_time_original,
                }.items() if v is not None
            },
            "source": self.source.to_dict(),
            "destination": self.destination.to_dict(),
            "network": self.network.to_dict(),
            "http": self.http.to_dict(),
            "event": self.event.to_dict(),
            "device": self.device.to_dict(),
            "observer": self.observer.to_dict(),
            "user": self.user.to_dict(),
            "extensions": self.extensions,
            "raw_ref": self.raw_ref.to_dict() if self.raw_ref else None,
        }
