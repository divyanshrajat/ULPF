from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class Source(Base):
    __tablename__ = "sources"
    source_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    transport = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    product = Column(String, nullable=True)
    namespace = Column(String, nullable=True)
    schema_pin = Column(String, nullable=True)
    format_pin = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    template_id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    pattern = Column(String, nullable=False)
    variable_positions = Column(JSONB, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    status = Column(String, nullable=False, default="active")

class Mapping(Base):
    __tablename__ = "mappings"
    mapping_id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    template_id = Column(String, ForeignKey("templates.template_id"))
    version = Column(Integer, nullable=False)
    field_bindings = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default="active")
    confidence_summary = Column(JSONB, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    superseded_by = Column(String, nullable=True)

class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    schema_version = Column(String, primary_key=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    field_definitions = Column(JSONB, nullable=False)
    compatibility_class = Column(String, nullable=False)
    checksum = Column(String, nullable=False)

class RawIndex(Base):
    __tablename__ = "raw_index"
    trace_id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    received_at = Column(DateTime, default=datetime.utcnow)
    transport = Column(String, nullable=False)
    peer = Column(String, nullable=True)
    byte_length = Column(Integer, nullable=False)
    digest = Column(String, nullable=False)
    storage_uri = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=True)

class Provenance(Base):
    __tablename__ = "provenance"
    trace_id = Column(String, ForeignKey("raw_index.trace_id"), primary_key=True)
    target_field = Column(String, primary_key=True)
    source_field = Column(String, nullable=False)
    source_value = Column(String, nullable=True)
    transformation = Column(String, nullable=False)
    mapping_id = Column(String, ForeignKey("mappings.mapping_id"), nullable=True)
    mapping_version = Column(Integer, nullable=True)
    schema_version = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    decision = Column(String, nullable=False)

class Audit(Base):
    __tablename__ = "audit"
    audit_id = Column(String, primary_key=True)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    subject_type = Column(String, nullable=False)
    subject_id = Column(String, nullable=False)
    before = Column(JSONB, nullable=True)
    after = Column(JSONB, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)

class DeadLetter(Base):
    __tablename__ = "dead_letters"
    trace_id = Column(String, primary_key=True)
    stage = Column(String, nullable=False)
    error_class = Column(String, nullable=False)
    diagnostic = Column(String, nullable=False)
    raw_reference = Column(String, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)
