import pytest
from app.models.domain import IngestionJob, RuleLock, RuleVersion, Rule
from app.api.jobs import create_job
from app.workers.processor import process_event
from app.core.queue import EventRecord
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
import uuid
from datetime import datetime

class MockActor:
    def get(self, key, default):
        if key == "tenant_id":
            return "default"
        return default

class MockBackgroundTasks:
    def add_task(self, func, *args, **kwargs):
        pass

class MockFile:
    async def read(self):
        return b'{"test":"1"}\n{"test":"2"}'

@pytest.mark.asyncio
async def test_batch_job_rulelock_lifecycle():
    db = SessionLocal()
    
    # 1. Setup a job using the API function
    source_id = "cloudtrail"
    bg_tasks = MockBackgroundTasks()
    m_file = MockFile()
    
    # Run the API method (which we fixed to create a RuleLock)
    res = await create_job(
        source_id=source_id,
        background_tasks=bg_tasks,
        file=m_file,
        db=db,
        actor=MockActor()
    )
    
    job_id = res["id"]
    
    # Verify the lock was created properly
    lock = db.query(RuleLock).filter(RuleLock.job_id == job_id).first()
    assert lock is not None, "RuleLock was not created for the batch job"
    assert lock.status == "SAMPLING"
    assert lock.sample_count_seen == 0
    
    # Create a rule and active version to simulate locking
    rule_id = str(uuid.uuid4())
    r = Rule(rule_id=rule_id, name="Test Rule", status="ACTIVE")
    rv = RuleVersion(id=str(uuid.uuid4()), rule_id=rule_id, version=1, parser_type="jsonpath", parser_definition={}, field_mappings={}, status="ACTIVE")
    db.add(r)
    db.add(rv)
    db.commit()

    # Create the raw index entries for process_event to find
    from app.models.domain import RawIndex
    for i in range(11):
        db.add(RawIndex(trace_id=f"trace-{job_id}-{i}", source_id=source_id, byte_length=100))
    db.commit()

    # Mock find_active_rule_by_fingerprint to return our active rule
    import app.workers.processor as processor
    original_find = processor.find_active_rule_by_fingerprint
    processor.find_active_rule_by_fingerprint = lambda db, fp: rv
    
    try:
        # Simulate processing 11 events to trigger locking (threshold is 10)
        for i in range(11):
            record = EventRecord(
                trace_id=f"trace-{job_id}-{i}",
                source_id=source_id,
                payload=b'{"test":"1"}',
                byte_length=100,
                received_at=datetime.utcnow(),
                transport="batch_api",
                job_id=job_id
            )
            await process_event(record)
            
        db.expire_all()
        
        lock = db.query(RuleLock).filter(RuleLock.job_id == job_id).first()
        
        # Verify lock transitioned
        assert lock.sample_count_seen == 11
        assert lock.status == "LOCKED"
        assert lock.rule_version_id == rv.id
        
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        assert job.processed_events == 11
        
        # Test idempotency (process same trace again)
        record = EventRecord(
            trace_id=f"trace-{job_id}-0",
            source_id=source_id,
            payload=b'{"test":"1"}',
            byte_length=100,
            received_at=datetime.utcnow(),
            transport="batch_api",
            job_id=job_id
        )
        await process_event(record)
        
        db.expire_all()
        lock = db.query(RuleLock).filter(RuleLock.job_id == job_id).first()
        assert lock.sample_count_seen == 11 # Should not increment because of idempotency check
        
    finally:
        processor.find_active_rule_by_fingerprint = original_find
        db.close()
