"""
processor.py — Background event processing worker.

Implements the full staged pipeline:
  S1 ingestion (done in gateway)
  S2 format detection
  S3 adaptive/fast discovery
  S4 field extraction + typing
  S5 semantic mapping + confidence
  S6 normalization
  S7 provenance
  S8 indexing (OpenSearch + PostgreSQL)

Each stage is persisted as a ProcessingStageRun.
Fast path vs Adaptive path is decided by backend state, not timing.
"""
import asyncio
import logging
import uuid
from datetime import datetime

from app.core.queue import event_queue
from app.core.database import SessionLocal
from app.services.detection.classifier import classify_format
from app.services.extraction.deterministic import (
    parse_json, parse_key_value, parse_delimited, parse_syslog_3164
)
from app.services.discovery.extraction_service import discover_and_extract
from app.services.typing.inference import infer_value_type
from app.services.mapping.semantic import semantic_mapper
from app.services.normalization.engine import normalization_engine
from app.services.provenance.layer import save_provenance
from app.models.domain import (
    DeadLetter, RawIndex, Mapping, ReviewItem, Template,
    ProcessingStageRun, NormalizedEvent
)
from app.core.opensearch import get_opensearch_client, index_event
from app.core.config import settings

logger = logging.getLogger(__name__)


def _make_stage_run(trace_id: str, stage: str) -> ProcessingStageRun:
    return ProcessingStageRun(
        id=str(uuid.uuid4()),
        trace_id=trace_id,
        stage=stage,
        status="RUNNING",
        started_at=datetime.utcnow(),
    )


def _complete_stage(db, run: ProcessingStageRun, output_ref: str = None):
    run.status = "COMPLETE"
    run.completed_at = datetime.utcnow()
    if run.started_at:
        run.duration_ms = (run.completed_at - run.started_at).total_seconds() * 1000
    run.output_reference = output_ref
    db.commit()


def _fail_stage(db, run: ProcessingStageRun, error_code: str, error_msg: str):
    run.status = "FAILED"
    run.completed_at = datetime.utcnow()
    if run.started_at:
        run.duration_ms = (run.completed_at - run.started_at).total_seconds() * 1000
    run.error_code = error_code
    run.error_message = error_msg[:500]
    db.commit()


async def process_event(record):
    db = SessionLocal()
    trace_id = record.trace_id
    source_id = record.source_id
    processing_path = "adaptive"  # default; overridden if fast path taken

    # S2: Format Detection
    stage_run = _make_stage_run(trace_id, "detection")
    db.add(stage_run)
    db.commit()

    try:
        detection = classify_format(record.payload)
        _complete_stage(db, stage_run, output_ref=f"format:{detection.format_name}:confidence:{detection.confidence:.2f}")
    except Exception as e:
        _fail_stage(db, stage_run, "DETECTION_ERROR", str(e))
        detection = None

    parsed_data = None
    template_id = None
    pattern = None

    # S3: Discovery / Parsing
    stage_run = _make_stage_run(trace_id, "discovery")
    db.add(stage_run)
    db.commit()

    try:
        # ── Fast path check ────────────────────────────────────────────────
        # Fast path = source known + template matched + approved mapping exists.
        # We determine this from DB state, not from timing.

        if detection and detection.confidence >= 0.90:
            # Try deterministic parsing
            if detection.format_name == "json":
                parsed_data = parse_json(record.payload)
            elif detection.format_name == "key_value":
                parsed_data = parse_key_value(record.payload)
            elif detection.format_name == "syslog_3164":
                parsed_data = parse_syslog_3164(record.payload)
            elif detection.format_name == "delimited_pipe":
                parsed_data = parse_delimited(record.payload, delimiter="|")

            if parsed_data:
                import hashlib
                keys_str = ",".join(sorted(parsed_data.keys()))
                key_hash = hashlib.md5(keys_str.encode()).hexdigest()[:12]
                template_id = f"tpl_{source_id}_fp_{key_hash}"
                pattern = f"FastPath:{detection.format_name}"

                # Ensure template exists in DB
                tmpl = db.query(Template).filter(Template.template_id == template_id).first()
                if not tmpl:
                    tmpl = Template(
                        template_id=template_id,
                        source_id=source_id,
                        pattern=pattern,
                        variable_positions={},
                        occurrence_count=1,
                    )
                    db.add(tmpl)
                else:
                    tmpl.occurrence_count = (tmpl.occurrence_count or 0) + 1
                db.commit()

        # Check if there is an approved mapping for this template
        active_mapping = None
        if template_id:
            active_mapping = (
                db.query(Mapping)
                .filter(
                    Mapping.source_id == source_id,
                    Mapping.template_id == template_id,
                    Mapping.status == "active",
                )
                .first()
            )

        if parsed_data and active_mapping:
            # ─ FAST PATH ─────────────────────────────────────────────────────
            processing_path = "fast"
            _complete_stage(db, stage_run, output_ref=f"fast_path:template:{template_id}")
        else:
            # ─ ADAPTIVE PATH ─────────────────────────────────────────────────
            processing_path = "adaptive"
            if parsed_data is None:
                # Run Drain3 discovery
                template_obj, candidates = discover_and_extract(db, source_id, record.payload)
                if not template_obj:
                    raise Exception("Format unknown and structure discovery failed. Cannot discover template.")
                template_id = template_obj.template_id
                pattern = template_obj.pattern
                parsed_data = {c.field_key: (c.sample_values[0] if c.sample_values else None) for c in candidates}
            else:
                # We have parsed_data but no approved mapping yet
                from app.schemas.domain import CandidateField
                candidates = [
                    CandidateField(field_key=k, position="0", sample_values=[str(v)])
                    for k, v in parsed_data.items()
                ]

            _complete_stage(db, stage_run, output_ref=f"adaptive_path:template:{template_id}")

    except Exception as e:
        _fail_stage(db, stage_run, "DISCOVERY_FAILED", str(e))
        _create_dead_letter(db, trace_id, source_id, "discovery", e)
        db.close()
        event_queue.task_done()
        return

    # S4: Extraction + Typing (for adaptive path)
    stage_run = _make_stage_run(trace_id, "extraction")
    db.add(stage_run)
    db.commit()

    candidates = []
    if processing_path == "adaptive":
        from app.schemas.domain import CandidateField
        for k, v in parsed_data.items():
            c = CandidateField(field_key=k, position="0", sample_values=[str(v)] if v is not None else [])
            c.inferred_type = infer_value_type(c.sample_values)
            candidates.append(c)
    _complete_stage(db, stage_run, output_ref=f"fields:{len(candidates)}")

    # S5: Mapping + Confidence
    stage_run = _make_stage_run(trace_id, "mapping")
    db.add(stage_run)
    db.commit()

    try:
        if processing_path == "adaptive":
            active_mapping = (
                db.query(Mapping)
                .filter(
                    Mapping.source_id == source_id,
                    Mapping.template_id == template_id,
                    Mapping.status == "active",
                )
                .first()
            )

            if not active_mapping:
                # Check drift: new fields vs existing mapping
                _handle_drift_and_review(db, source_id, template_id, pattern, candidates)
                _complete_stage(db, stage_run, output_ref="review_required")
            else:
                # Check for drift in an approved mapping
                unmapped = [c for c in candidates if c.field_key not in active_mapping.field_bindings]
                if unmapped:
                    _handle_drift(db, source_id, template_id, pattern, unmapped)
                _complete_stage(db, stage_run, output_ref=f"mapping:{active_mapping.mapping_id}:v{active_mapping.version}")
        else:
            # Fast path — mapping already confirmed above
            _complete_stage(db, stage_run, output_ref=f"fast_path_mapping:{template_id}")

    except Exception as e:
        _fail_stage(db, stage_run, "MAPPING_ERROR", str(e))
        # Don't dead letter here; continue to normalization with whatever mapping exists

    # S6: Normalization
    stage_run = _make_stage_run(trace_id, "normalization")
    db.add(stage_run)
    db.commit()

    try:
        raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
        digest = raw_idx.digest if raw_idx else "sha256:unknown"

        raw_ref = {
            "trace_id": trace_id,
            "digest": digest,
            "byte_length": record.byte_length,
        }

        normalized_event, provenance_records = normalization_engine.normalize(
            db=db,
            parsed_data=parsed_data,
            source_id=source_id,
            template_id=template_id,
            trace_id=trace_id,
            raw_ref=raw_ref,
        )

        # Persist NormalizedEvent to PostgreSQL
        ne = NormalizedEvent(
            event_id=str(uuid.uuid4()),
            trace_id=trace_id,
            source_id=source_id,
            schema_version="ulpf-core-1.0",
            mapping_id=normalized_event.metadata.get("mapping_id"),
            mapping_version=normalized_event.metadata.get("mapping_version"),
            processing_path=processing_path,
            normalized_payload=normalized_event.dict(),
            created_at=datetime.utcnow(),
        )
        db.add(ne)
        db.commit()

        _complete_stage(db, stage_run, output_ref=f"event:{ne.event_id}")

    except Exception as e:
        _fail_stage(db, stage_run, "NORMALIZATION_ERROR", str(e))
        _create_dead_letter(db, trace_id, source_id, "normalization", e)
        db.close()
        event_queue.task_done()
        return

    # S7: Provenance
    stage_run = _make_stage_run(trace_id, "provenance")
    db.add(stage_run)
    db.commit()
    try:
        save_provenance(db, provenance_records)
        _complete_stage(db, stage_run, output_ref=f"provenance_records:{len(provenance_records)}")
    except Exception as e:
        _fail_stage(db, stage_run, "PROVENANCE_ERROR", str(e))

    # S8: Index to OpenSearch
    stage_run = _make_stage_run(trace_id, "indexing")
    db.add(stage_run)
    db.commit()
    try:
        from app.core.time import to_ist_iso
        os_client = get_opensearch_client()
        event_dict = normalized_event.dict()
        event_dict["trace_id"] = trace_id
        event_dict["source_id"] = source_id
        event_dict["processing_path"] = processing_path
        event_dict["@timestamp"] = to_ist_iso()
        index_event(os_client, event_dict)
        _complete_stage(db, stage_run, output_ref=f"opensearch:{settings.OPENSEARCH_INDEX}")
    except Exception as e:
        # OpenSearch failure is non-fatal; data is in PostgreSQL
        _fail_stage(db, stage_run, "OPENSEARCH_UNAVAILABLE", str(e))
        logger.warning(f"OpenSearch indexing failed for trace {trace_id}: {e} — data preserved in PostgreSQL")

    logger.info(
        f"[PIPELINE COMPLETE] trace_id={trace_id} source={source_id} "
        f"path={processing_path} template={template_id}"
    )

    db.close()
    event_queue.task_done()


def _handle_drift_and_review(db, source_id, template_id, pattern, candidates):
    """Create review items for unmapped fields when no approved mapping exists."""
    pending = (
        db.query(ReviewItem)
        .filter(
            ReviewItem.source_id == source_id,
            ReviewItem.template_id == template_id,
            ReviewItem.status.in_(["PENDING", "IN_REVIEW"]),
        )
        .first()
    )
    if pending:
        return  # Already in review

    proposals = []
    for cand in candidates:
        if not cand.inferred_type:
            cand.inferred_type = infer_value_type(cand.sample_values)
        props = semantic_mapper.propose_mappings(db, source_id, template_id, cand, pattern or "")
        if props:
            top = props[0]
            proposals.append({
                "source_field": cand.field_key,
                "position": cand.position,
                "inferred_type": cand.inferred_type,
                "sample_value": cand.sample_values[0] if cand.sample_values else None,
                "proposed_target": top.target_field,
                "confidence": top.confidence,
                "decision": top.decision,
                "signals": top.signals,
            })

    if proposals:
        high_conf = max(p["confidence"] for p in proposals)
        review = ReviewItem(
            review_id=str(uuid.uuid4()),
            source_id=source_id,
            template_id=template_id,
            pattern=pattern or "",
            proposals=proposals,
            confidence=high_conf,
            reason="New source/template requires mapping review",
            status="PENDING",
            created_at=datetime.utcnow(),
        )
        db.add(review)
        db.commit()


def _handle_drift(db, source_id, template_id, pattern, unmapped_candidates):
    """Detect and create drift review items for new fields in a known template."""
    drift_template_id = f"{template_id}_drift_{datetime.utcnow().strftime('%Y%m%d')}"
    pending = (
        db.query(ReviewItem)
        .filter(ReviewItem.source_id == source_id, ReviewItem.template_id == drift_template_id)
        .first()
    )
    if pending:
        return

    proposals = []
    for cand in unmapped_candidates:
        if not cand.inferred_type:
            cand.inferred_type = infer_value_type(cand.sample_values)
        props = semantic_mapper.propose_mappings(db, source_id, template_id, cand, pattern or "")
        if props:
            top = props[0]
            proposals.append({
                "source_field": cand.field_key,
                "position": cand.position,
                "inferred_type": cand.inferred_type,
                "sample_value": cand.sample_values[0] if cand.sample_values else None,
                "proposed_target": top.target_field,
                "confidence": top.confidence,
                "decision": "review",
                "signals": top.signals,
            })

    if proposals:
        review = ReviewItem(
            review_id=str(uuid.uuid4()),
            source_id=source_id,
            template_id=drift_template_id,
            pattern=f"DRIFT: {pattern}",
            proposals=proposals,
            confidence=max(p["confidence"] for p in proposals),
            reason="Schema drift detected: new fields appeared in known source",
            status="PENDING",
            created_at=datetime.utcnow(),
        )
        db.add(review)
        db.commit()
        logger.warning(f"[DRIFT DETECTED] source={source_id} template={template_id} new_fields={[c.field_key for c in unmapped_candidates]}")


def _create_dead_letter(db, trace_id, source_id, stage, error):
    """Create a dead letter record — raw bytes are already preserved in vault."""
    try:
        from app.models.domain import RawIndex
        raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
        raw_ref = raw_idx.storage_uri if raw_idx else f"vault://{source_id}/unknown/{trace_id}.raw"

        existing = db.query(DeadLetter).filter(DeadLetter.trace_id == trace_id).first()
        if not existing:
            dl = DeadLetter(
                trace_id=trace_id,
                source_id=source_id,
                stage=stage,
                error_class=error.__class__.__name__,
                diagnostic=str(error)[:500],
                raw_reference=raw_ref,
                created_at=datetime.utcnow(),
            )
            db.add(dl)
            db.commit()
    except Exception as inner_e:
        logger.error(f"Failed to create dead letter for {trace_id}: {inner_e}")


async def worker_loop():
    logger.info("ULPF processing worker started.")
    while True:
        try:
            record = await event_queue.pop()
            await process_event(record)
        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            await asyncio.sleep(1)
