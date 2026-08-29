from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class Source(Base):
    __tablename__ = "sources"
    source_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    product = Column(String, nullable=True)
    transport = Column(String, nullable=False, default="http")
    format_hint = Column(String, nullable=True)
    namespace = Column(String, nullable=True)
    schema_pin = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active") # active, paused, disabled, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)
    active_mapping_version = Column(Integer, nullable=True)
    active_schema_version = Column(String, nullable=True)

class File(Base):
    __tablename__ = "files"
    file_id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=False)
    sha256 = Column(String, nullable=False)
    storage_uri = Column(String, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False, default="pending")
    analysis_session_id = Column(String, nullable=True)
    trace_ids = Column(JSONB, nullable=True)
    format = Column(String, nullable=True)
    template_id = Column(String, ForeignKey("templates.template_id"), nullable=True)
    mapping_id = Column(String, ForeignKey("mappings.mapping_id"), nullable=True)
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

class ReviewItem(Base):
    __tablename__ = "review_items"
    review_id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    template_id = Column(String, ForeignKey("templates.template_id"))
    field_id = Column(String, nullable=True)
    pattern = Column(String, nullable=False)
    proposals = Column(JSONB, nullable=False)
    confidence = Column(Float, nullable=True)
    confidence_components = Column(JSONB, nullable=True)
    reason = Column(String, nullable=True)
    priority = Column(Integer, default=1)
    status = Column(String, nullable=False, default="PENDING") # PENDING, IN_REVIEW, APPROVED, REASSIGNED, EXTENSION_ONLY, REJECTED
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

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
    source_id = Column(String, ForeignKey("sources.source_id"), nullable=True)
    stage = Column(String, nullable=False)
    error_class = Column(String, nullable=False)
    diagnostic = Column(String, nullable=False)
    raw_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Trace(Base):
    __tablename__ = "traces"
    trace_id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    file_id = Column(String, ForeignKey("files.file_id"), nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)

class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    file_id = Column(String, ForeignKey("files.file_id"))
    current_stage = Column(String, nullable=False, default="SOURCE_SELECTION")
    status = Column(String, nullable=False, default="STARTED")
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    trace_id = Column(String, nullable=True)

class ProcessingStageRun(Base):
    __tablename__ = "processing_stage_runs"
    id = Column(String, primary_key=True)
    trace_id = Column(String, ForeignKey("traces.trace_id"))
    stage = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    input_reference = Column(String, nullable=True)
    output_reference = Column(String, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

class Field(Base):
    __tablename__ = "fields"
    field_id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("templates.template_id"))
    source_name = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    sample_value = Column(String, nullable=True)
    inferred_type = Column(String, nullable=True)
    type_confidence = Column(Float, nullable=True)
    frequency = Column(Integer, default=1)
    evidence = Column(JSONB, nullable=True)

class NormalizedEvent(Base):
    __tablename__ = "normalized_events"
    event_id = Column(String, primary_key=True)
    trace_id = Column(String, ForeignKey("traces.trace_id"))
    source_id = Column(String, ForeignKey("sources.source_id"))
    schema_version = Column(String, nullable=False)
    mapping_id = Column(String, ForeignKey("mappings.mapping_id"), nullable=True)
    mapping_version = Column(Integer, nullable=True)
    processing_path = Column(String, nullable=False) # 'fast' or 'adaptive'
    normalized_payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
