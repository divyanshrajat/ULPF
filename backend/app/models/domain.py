from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

# Dialect-agnostic JSON type: uses JSONB on PostgreSQL, standard JSON on SQLite/others
JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")

# ─── CORE ────────────────────────────────────────────────────────────────────────

class Source(Base):
    __tablename__ = "sources"
    source_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    product = Column(String, nullable=True)
    transport = Column(String, nullable=False, default="http")
    format_hint = Column(String, nullable=True)
    namespace = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active") # active, paused, disabled, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)

class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    schema_version = Column(String, primary_key=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    field_definitions = Column(JSON_TYPE, nullable=False)
    compatibility_class = Column(String, nullable=False)
    checksum = Column(String, nullable=False)

# ─── RULES ───────────────────────────────────────────────────────────────────────

class Rule(Base):
    __tablename__ = "rules"
    rule_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="DRAFT") # DRAFT, PENDING_REVIEW, ACTIVE, DEPRECATED, DISABLED, ARCHIVED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RuleVersion(Base):
    __tablename__ = "rule_versions"
    id = Column(String, primary_key=True)
    rule_id = Column(String, ForeignKey("rules.rule_id"), nullable=False)
    version = Column(Integer, nullable=False)
    parser_type = Column(String, nullable=False)
    parser_definition = Column(JSON_TYPE, nullable=False)
    field_mappings = Column(JSON_TYPE, nullable=False)
    required_fields = Column(JSON_TYPE, nullable=True)
    type_constraints = Column(JSON_TYPE, nullable=True)
    masking_policy = Column(JSON_TYPE, nullable=True)
    target_schema = Column(String, nullable=False, default="ocsf")
    schema_version = Column(String, nullable=False)
    rule_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="DRAFT") # DRAFT, PENDING_REVIEW, ACTIVE, DEPRECATED
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    rule = relationship("Rule")

class RuleFingerprint(Base):
    __tablename__ = "rule_fingerprints"
    id = Column(String, primary_key=True)
    rule_id = Column(String, ForeignKey("rules.rule_id"), nullable=False)
    fingerprint = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RuleTestCase(Base):
    __tablename__ = "rule_test_cases"
    id = Column(String, primary_key=True)
    rule_version_id = Column(String, ForeignKey("rule_versions.id"), nullable=False)
    raw_sample = Column(String, nullable=False)
    expected_output = Column(JSON_TYPE, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RuleValidationRun(Base):
    __tablename__ = "rule_validation_runs"
    id = Column(String, primary_key=True)
    rule_version_id = Column(String, ForeignKey("rule_versions.id"), nullable=False)
    passed = Column(Boolean, nullable=False)
    results = Column(JSON_TYPE, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RuleApproval(Base):
    __tablename__ = "rule_approvals"
    id = Column(String, primary_key=True)
    rule_version_id = Column(String, ForeignKey("rule_versions.id"), nullable=False)
    reviewer = Column(String, nullable=False)
    decision = Column(String, nullable=False) # APPROVED, REJECTED
    comments = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RuleLifecycleEvent(Base):
    __tablename__ = "rule_lifecycle_events"
    id = Column(String, primary_key=True)
    rule_id = Column(String, ForeignKey("rules.rule_id"), nullable=False)
    rule_version_id = Column(String, ForeignKey("rule_versions.id"), nullable=True)
    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class RuleLLMGeneration(Base):
    __tablename__ = "rule_llm_generations"
    id = Column(String, primary_key=True)
    rule_version_id = Column(String, ForeignKey("rule_versions.id"), nullable=True)
    prompt = Column(String, nullable=False)
    response_json = Column(String, nullable=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ─── DATA PLANE (PRESERVATION & NORMALIZATION) ───────────────────────────────────

class RawIndex(Base):
    __tablename__ = "raw_index"
    trace_id = Column(String, primary_key=True) # event_id
    source_id = Column(String, ForeignKey("sources.source_id"))
    received_at = Column(DateTime, default=datetime.utcnow)
    transport = Column(String, nullable=False)
    peer = Column(String, nullable=True)
    byte_length = Column(Integer, nullable=False)
    digest = Column(String, nullable=False) # sha256
    storage_uri = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    job_id = Column(String, ForeignKey("ingestion_jobs.id"), nullable=True)
    session_id = Column(String, ForeignKey("ingestion_sessions.id"), nullable=True)

class Trace(Base):
    __tablename__ = "traces"
    trace_id = Column(String, primary_key=True) # event_id
    source_id = Column(String, ForeignKey("sources.source_id"))
    received_at = Column(DateTime, default=datetime.utcnow)
    rule_id = Column(String, ForeignKey("rules.rule_id"), nullable=True)
    rule_version = Column(Integer, nullable=True)
    rule_hash = Column(String, nullable=True)
    schema_version = Column(String, nullable=True)
    job_id = Column(String, ForeignKey("ingestion_jobs.id"), nullable=True)
    session_id = Column(String, ForeignKey("ingestion_sessions.id"), nullable=True)

class NormalizedEvent(Base):
    __tablename__ = "normalized_events"
    event_id = Column(String, primary_key=True)
    trace_id = Column(String, ForeignKey("traces.trace_id"))
    source_id = Column(String, ForeignKey("sources.source_id"))
    schema_version = Column(String, nullable=False)
    rule_id = Column(String, ForeignKey("rules.rule_id"), nullable=True)
    rule_version = Column(Integer, nullable=True)
    processing_path = Column(String, nullable=False) # 'fast_path', 'onboarding', 'unresolved'
    normalized_payload = Column(JSON_TYPE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    job_id = Column(String, ForeignKey("ingestion_jobs.id"), nullable=True)
    session_id = Column(String, ForeignKey("ingestion_sessions.id"), nullable=True)

class UnresolvedEvent(Base):
    __tablename__ = "unresolved_events"
    id = Column(String, primary_key=True)
    trace_id = Column(String, ForeignKey("traces.trace_id"))
    fingerprint = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    job_id = Column(String, ForeignKey("ingestion_jobs.id"), nullable=True)
    session_id = Column(String, ForeignKey("ingestion_sessions.id"), nullable=True)

# ─── CONTROL PLANE & OPERATIONS ──────────────────────────────────────────────────

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    status = Column(String, nullable=False, default="STARTED")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_events = Column(Integer, default=0)
    processed_events = Column(Integer, default=0)
    normalized_count = Column(Integer, default=0)
    unresolved_count = Column(Integer, default=0)

class IngestionSession(Base):
    __tablename__ = "ingestion_sessions"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    status = Column(String, nullable=False, default="ACTIVE")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_events = Column(Integer, default=0)
    processed_events = Column(Integer, default=0)
    normalized_count = Column(Integer, default=0)
    unresolved_count = Column(Integer, default=0)

class RuleLock(Base):
    __tablename__ = "rule_locks"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("ingestion_sessions.id"), nullable=True)
    job_id = Column(String, ForeignKey("ingestion_jobs.id"), nullable=True)
    rule_version_id = Column(String, ForeignKey("rule_versions.id"))
    fingerprint = Column(String, nullable=True)
    sample_count_seen = Column(Integer, default=0)
    mismatch_count = Column(Integer, default=0)
    events_since_lock = Column(Integer, default=0)
    events_since_mismatch = Column(Integer, default=0)
    status = Column(String, nullable=False, default="SAMPLING") # SAMPLING, LOCKED, UNLOCKED
    created_at = Column(DateTime, default=datetime.utcnow)

class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.source_id"))
    fingerprint = Column(String, nullable=True)
    rule_id = Column(String, ForeignKey("rules.rule_id"), nullable=True)
    status = Column(String, nullable=False, default="STARTED")
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Audit(Base):
    __tablename__ = "audit"
    audit_id = Column(String, primary_key=True)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    subject_type = Column(String, nullable=False)
    subject_id = Column(String, nullable=False)
    before = Column(JSON_TYPE, nullable=True)
    after = Column(JSON_TYPE, nullable=True)
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

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True)
    key_hash = Column(String, nullable=False)
    masked_key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    source_scope = Column(String, nullable=True)
    environment = Column(String, nullable=False, default="production")
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

