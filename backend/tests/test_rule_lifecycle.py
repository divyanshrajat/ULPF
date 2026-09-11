"""
T42 — Rule lifecycle tests:
  - reject/disable/archive transitions
  - one-active-version race condition (concurrent approve)
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.domain import Rule, RuleVersion, RuleLifecycleEvent, RuleApproval
from app.services.rules.registry import update_rule_version_status, create_rule_version, create_rule


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_rule_version(db, rule_id: str, version: int, status: str = "PENDING_REVIEW") -> RuleVersion:
    v = RuleVersion(
        id=str(uuid.uuid4()),
        rule_id=rule_id,
        version=version,
        parser_type="regex",
        parser_definition={"pattern": "(?P<msg>.*)"},
        field_mappings={"msg": "message"},
        required_fields=["msg"],
        target_schema="ocsf",
        schema_version="1.0",
        rule_hash=f"hash{version}",
        status=status,
    )
    db.add(v)
    db.commit()
    return v


# ── tests ─────────────────────────────────────────────────────────────────────

def test_reject_transitions_status_to_rejected():
    db = SessionLocal()
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name="Lifecycle Test", status="DRAFT")
    db.add(rule)
    db.commit()

    v1 = _make_rule_version(db, rule_id, 1, status="PENDING_REVIEW")
    update_rule_version_status(db, v1.id, "REJECTED", actor="tester")

    db.refresh(v1)
    assert v1.status == "REJECTED"

    # Verify a RuleLifecycleEvent was written with the actor
    event = db.query(RuleLifecycleEvent).filter(
        RuleLifecycleEvent.rule_version_id == v1.id,
        RuleLifecycleEvent.event_type == "STATUS_CHANGED_TO_REJECTED",
    ).first()
    assert event is not None
    assert event.actor == "tester"

    db.delete(v1)
    db.delete(rule)
    db.commit()
    db.close()


def test_disable_rule_deactivates_active_version():
    db = SessionLocal()
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name="Disable Test", status="ACTIVE")
    db.add(rule)
    db.commit()

    # Create and activate a version
    v1 = _make_rule_version(db, rule_id, 1, status="PENDING_REVIEW")
    update_rule_version_status(db, v1.id, "ACTIVE", actor="approver")

    db.refresh(v1)
    assert v1.status == "ACTIVE"

    # Now disable the version
    update_rule_version_status(db, v1.id, "DISABLED", actor="admin")

    db.refresh(v1)
    assert v1.status == "DISABLED"

    db.delete(v1)
    db.delete(rule)
    db.commit()
    db.close()


def test_archive_rule_removes_from_active_lookup():
    db = SessionLocal()
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name="Archive Test", status="ACTIVE")
    db.add(rule)
    db.commit()

    v1 = _make_rule_version(db, rule_id, 1, status="PENDING_REVIEW")
    update_rule_version_status(db, v1.id, "ACTIVE", actor="approver")
    update_rule_version_status(db, v1.id, "ARCHIVED", actor="admin")

    db.refresh(v1)
    assert v1.status == "ARCHIVED"

    # No ACTIVE version should remain
    active = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.status == "ACTIVE"
    ).first()
    assert active is None

    db.delete(v1)
    db.delete(rule)
    db.commit()
    db.close()


def test_one_active_version_constraint_on_concurrent_approve():
    """
    Two versions of the same rule cannot both be ACTIVE simultaneously.
    The second activation must raise an IntegrityError (partial unique index).
    """
    db = SessionLocal()
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name="Concurrent Approve Test", status="DRAFT")
    db.add(rule)
    db.commit()

    v1 = _make_rule_version(db, rule_id, 1, status="PENDING_REVIEW")
    v2 = _make_rule_version(db, rule_id, 2, status="PENDING_REVIEW")

    # Approve v1 — OK
    update_rule_version_status(db, v1.id, "ACTIVE", actor="approver")
    db.refresh(v1)
    assert v1.status == "ACTIVE"

    # Directly try to set v2 ACTIVE without going through registry
    # (simulates a concurrent bypass that doesn't call update_rule_version_status)
    v2.status = "ACTIVE"
    db.add(v2)
    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()
    db.delete(v2)
    db.delete(v1)
    db.delete(rule)
    db.commit()
    db.close()
