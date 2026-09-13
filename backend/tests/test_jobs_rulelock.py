"""
test_jobs_rulelock.py — Self-contained RuleLock lifecycle test for batch jobs.

Creates all required DB rows itself (Source, Tenant, Rule, RuleVersion,
RawIndex, IngestionJob, RuleLock) so the test does NOT depend on seed data,
execution order, or a pre-existing "cloudtrail" source.

Uses IngestRecord (not EventRecord) because process_event() reads
record.job_id to look up the associated RuleLock.
"""

import asyncio
import hashlib
import uuid
from datetime import datetime

import pytest

from app.core.database import SessionLocal
from app.models.domain import (
    IngestionJob,
    RawIndex,
    Rule,
    RuleLock,
    RuleVersion,
    Source,
    Tenant,
)
from app.schemas.domain import IngestRecord
from app.workers.processor import process_event


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_rule_version(db, rule_id: str) -> RuleVersion:
    """Create a minimal but fully-valid ACTIVE RuleVersion."""
    rv = RuleVersion(
        id=str(uuid.uuid4()),
        tenant_id="default",
        rule_id=rule_id,
        version=1,
        parser_type="regex",
        parser_definition={"pattern": r"(?P<msg>.+)", "flags": []},
        field_mappings={},
        required_fields=[],
        type_constraints={},
        masking_policy={},
        target_schema="ocsf",
        schema_version="ocsf-1.1.0",   # <-- required field
        rule_hash=hashlib.sha256(b"test").hexdigest(),
        status="ACTIVE",
    )
    db.add(rv)
    return rv


def _make_ingest_record(trace_id: str, source_id: str, job_id: str) -> IngestRecord:
    """Create an IngestRecord that carries job_id for the RuleLock lookup."""
    return IngestRecord(
        trace_id=trace_id,
        source_id=source_id,
        payload=b'{"event": "test"}',
        byte_length=17,
        received_at=datetime.utcnow(),
        transport="batch_api",       # required field
        peer=None,
        session_id=None,
        job_id=job_id,               # critical — wires event to the job RuleLock
    )


# ── test ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_job_rulelock_lifecycle():
    db = SessionLocal()

    try:
        # ── 1. Seed: Tenant, Source ──────────────────────────────────────────
        source_id = f"test-src-{uuid.uuid4().hex[:8]}"

        # Ensure the "default" tenant row exists (idempotent)
        from app.models.domain import Tenant
        if not db.query(Tenant).filter(Tenant.id == "default").first():
            db.add(Tenant(id="default", name="Default Tenant"))
            db.commit()

        source = Source(
            source_id=source_id,
            tenant_id="default",
            name="Test Batch Source",
            vendor="test",
            transport="batch_api",
            status="active",
        )
        db.add(source)
        db.commit()

        # ── 2. Seed: Rule + RuleVersion ──────────────────────────────────────
        rule_id = str(uuid.uuid4())
        rule = Rule(
            rule_id=rule_id,
            tenant_id="default",
            name=f"TestRule-{rule_id[:8]}",
            status="ACTIVE",
        )
        db.add(rule)
        rv = _make_rule_version(db, rule_id)
        db.commit()

        # ── 3. Create a batch job + its RuleLock ────────────────────────────
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            id=job_id,
            tenant_id="default",
            source_id=source_id,
            status="STARTED",
        )
        db.add(job)
        lock = RuleLock(
            id=str(uuid.uuid4()),
            job_id=job_id,
            rule_version_id=None,
            status="SAMPLING",
            sample_count_seen=0,
        )
        db.add(lock)
        db.commit()

        # ── 4. Verify initial RuleLock state ─────────────────────────────────
        db.expire_all()
        lock = db.query(RuleLock).filter(RuleLock.job_id == job_id).first()
        assert lock is not None, "RuleLock was not created for the batch job"
        assert lock.status == "SAMPLING"
        assert lock.sample_count_seen == 0

        # ── 5. Mock fingerprint lookup → always return our RuleVersion ───────
        #      Also patch event_queue.ack because process_event() calls it at
        #      the end; our IngestRecord was never put() into the queue so
        #      ack() → task_done() would raise ValueError.
        import app.workers.processor as processor_module
        import app.core.queue as queue_module
        original_find = processor_module.find_active_rule_by_fingerprint
        original_ack = queue_module.event_queue.ack
        processor_module.find_active_rule_by_fingerprint = lambda db, fp: rv
        queue_module.event_queue.ack = lambda record: None  # no-op for direct calls

        try:
            THRESHOLD = 10  # confirmed from processor.py: >= 10 → LOCKED

            # ── 6. Process THRESHOLD events — each needs its own RawIndex ────
            for i in range(THRESHOLD):
                trace_id = f"trace-{job_id}-{i}"

                db.add(RawIndex(
                    trace_id=trace_id,
                    source_id=source_id,
                    transport="batch_api",                            # required
                    digest=f"sha256:{hashlib.sha256(trace_id.encode()).hexdigest()}",  # required
                    storage_uri=f"vault://{source_id}/2026-09-13/{trace_id}.raw",    # required
                    byte_length=17,
                ))
            db.commit()

            for i in range(THRESHOLD):
                trace_id = f"trace-{job_id}-{i}"
                rec = _make_ingest_record(trace_id, source_id, job_id)
                await process_event(rec)

            db.expire_all()
            lock = db.query(RuleLock).filter(RuleLock.job_id == job_id).first()

            # ── 7. After threshold: must be LOCKED ───────────────────────────
            assert lock.status == "LOCKED", (
                f"Expected LOCKED after {THRESHOLD} matching events, got {lock.status}"
            )
            assert lock.rule_version_id == rv.id, (
                f"Expected rule_version_id={rv.id}, got {lock.rule_version_id}"
            )
            # sample_count_seen exactly equals threshold (the 10th increments it to 10
            # and then the transition fires — counter is NOT reset on LOCKED transition
            # per current processor.py logic, but events_since_lock resets to 0)
            assert lock.sample_count_seen == THRESHOLD, (
                f"Expected sample_count_seen={THRESHOLD}, got {lock.sample_count_seen}"
            )

            # ── 8. Job counters ───────────────────────────────────────────────
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            assert job.processed_events == THRESHOLD

            # ── 9. Idempotency: re-process trace-0, counters must not change ─
            existing_sample_count = lock.sample_count_seen
            existing_processed = job.processed_events

            duplicate_rec = _make_ingest_record(f"trace-{job_id}-0", source_id, job_id)
            await process_event(duplicate_rec)

            db.expire_all()
            lock = db.query(RuleLock).filter(RuleLock.job_id == job_id).first()
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()

            assert lock.sample_count_seen == existing_sample_count, (
                "Idempotency failed: sample_count_seen incremented on duplicate event"
            )
            assert job.processed_events == existing_processed, (
                "Idempotency failed: processed_events incremented on duplicate event"
            )

        finally:
            processor_module.find_active_rule_by_fingerprint = original_find
            queue_module.event_queue.ack = original_ack

    finally:
        db.close()
