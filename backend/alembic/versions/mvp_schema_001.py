"""
Complete MVP schema — adds all missing tables for ULPF v1.0 MVP.

Adds:
  - traces (was missing)
  - onboarding_sessions
  - processing_stage_runs
  - fields (field extraction results)
  - normalized_events
  - Updates sources (updated_at, active_schema_version, format_hint)
  - Updates files (received_at, storage_uri, status, mime_type, template_id, mapping_id, analysis_session_id)
  - Updates review_items (confidence, reason, priority, assigned_to, reviewed_at, field_id)
  - Updates dead_letters (source_id, created_at -> renamed from occurred_at)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'mvp_schema_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ── sources: add new columns ──────────────────────────────────────────────
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('format_hint', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('active_schema_version', sa.String(), nullable=True))

    # ── files: rebuild with new columns ──────────────────────────────────────
    # Check if table exists; if so, alter it
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_file_cols = [c['name'] for c in inspector.get_columns('files')]

    with op.batch_alter_table('files', schema=None) as batch_op:
        if 'mime_type' not in existing_file_cols:
            batch_op.add_column(sa.Column('mime_type', sa.String(), nullable=True))
        if 'storage_uri' not in existing_file_cols:
            batch_op.add_column(sa.Column('storage_uri', sa.String(), nullable=True))
        if 'received_at' not in existing_file_cols:
            batch_op.add_column(sa.Column('received_at', sa.DateTime(), nullable=True))
        if 'status' not in existing_file_cols:
            batch_op.add_column(sa.Column('status', sa.String(), server_default='pending', nullable=False))
        if 'analysis_session_id' not in existing_file_cols:
            batch_op.add_column(sa.Column('analysis_session_id', sa.String(), nullable=True))
        if 'template_id' not in existing_file_cols:
            batch_op.add_column(sa.Column('template_id', sa.String(), nullable=True))
        if 'mapping_id' not in existing_file_cols:
            batch_op.add_column(sa.Column('mapping_id', sa.String(), nullable=True))
        if 'created_at' not in existing_file_cols:
            batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    # ── review_items: add new columns ────────────────────────────────────────
    existing_review_cols = [c['name'] for c in inspector.get_columns('review_items')]
    with op.batch_alter_table('review_items', schema=None) as batch_op:
        if 'field_id' not in existing_review_cols:
            batch_op.add_column(sa.Column('field_id', sa.String(), nullable=True))
        if 'confidence' not in existing_review_cols:
            batch_op.add_column(sa.Column('confidence', sa.Float(), nullable=True))
        if 'confidence_components' not in existing_review_cols:
            batch_op.add_column(sa.Column('confidence_components', postgresql.JSONB(), nullable=True))
        if 'reason' not in existing_review_cols:
            batch_op.add_column(sa.Column('reason', sa.String(), nullable=True))
        if 'priority' not in existing_review_cols:
            batch_op.add_column(sa.Column('priority', sa.Integer(), server_default='1', nullable=True))
        if 'assigned_to' not in existing_review_cols:
            batch_op.add_column(sa.Column('assigned_to', sa.String(), nullable=True))
        if 'reviewed_at' not in existing_review_cols:
            batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))

    # ── dead_letters: add source_id ───────────────────────────────────────────
    existing_dl_cols = [c['name'] for c in inspector.get_columns('dead_letters')]
    with op.batch_alter_table('dead_letters', schema=None) as batch_op:
        if 'source_id' not in existing_dl_cols:
            batch_op.add_column(sa.Column('source_id', sa.String(), nullable=True))
        if 'created_at' not in existing_dl_cols and 'occurred_at' in existing_dl_cols:
            batch_op.alter_column('occurred_at', new_column_name='created_at')
        elif 'created_at' not in existing_dl_cols:
            batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    # ── traces (new table) ────────────────────────────────────────────────────
    existing_tables = inspector.get_table_names()
    if 'traces' not in existing_tables:
        op.create_table(
            'traces',
            sa.Column('trace_id', sa.String(), primary_key=True),
            sa.Column('source_id', sa.String(), sa.ForeignKey('sources.source_id'), nullable=False),
            sa.Column('file_id', sa.String(), nullable=True),
            sa.Column('received_at', sa.DateTime(), nullable=True),
        )

    # ── onboarding_sessions (new table) ──────────────────────────────────────
    if 'onboarding_sessions' not in existing_tables:
        op.create_table(
            'onboarding_sessions',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('source_id', sa.String(), sa.ForeignKey('sources.source_id'), nullable=False),
            sa.Column('file_id', sa.String(), nullable=True),
            sa.Column('current_stage', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('error_code', sa.String(), nullable=True),
            sa.Column('error_message', sa.String(), nullable=True),
            sa.Column('trace_id', sa.String(), nullable=True),
        )

    # ── processing_stage_runs (new table) ────────────────────────────────────
    if 'processing_stage_runs' not in existing_tables:
        op.create_table(
            'processing_stage_runs',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('trace_id', sa.String(), sa.ForeignKey('raw_index.trace_id'), nullable=False),
            sa.Column('stage', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('duration_ms', sa.Float(), nullable=True),
            sa.Column('input_reference', sa.String(), nullable=True),
            sa.Column('output_reference', sa.String(), nullable=True),
            sa.Column('error_code', sa.String(), nullable=True),
            sa.Column('error_message', sa.String(), nullable=True),
        )

    # ── fields (new table) ───────────────────────────────────────────────────
    if 'fields' not in existing_tables:
        op.create_table(
            'fields',
            sa.Column('field_id', sa.String(), primary_key=True),
            sa.Column('template_id', sa.String(), sa.ForeignKey('templates.template_id'), nullable=False),
            sa.Column('source_name', sa.String(), nullable=False),
            sa.Column('position', sa.Integer(), nullable=False),
            sa.Column('sample_value', sa.String(), nullable=True),
            sa.Column('inferred_type', sa.String(), nullable=True),
            sa.Column('type_confidence', sa.Float(), nullable=True),
            sa.Column('frequency', sa.Integer(), nullable=True),
            sa.Column('evidence', postgresql.JSONB(), nullable=True),
        )

    # ── normalized_events (new table) ────────────────────────────────────────
    if 'normalized_events' not in existing_tables:
        op.create_table(
            'normalized_events',
            sa.Column('event_id', sa.String(), primary_key=True),
            sa.Column('trace_id', sa.String(), nullable=False),
            sa.Column('source_id', sa.String(), sa.ForeignKey('sources.source_id'), nullable=False),
            sa.Column('schema_version', sa.String(), nullable=False),
            sa.Column('mapping_id', sa.String(), nullable=True),
            sa.Column('mapping_version', sa.Integer(), nullable=True),
            sa.Column('processing_path', sa.String(), nullable=False),
            sa.Column('normalized_payload', postgresql.JSONB(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )


def downgrade():
    # Drop new tables only
    op.drop_table('normalized_events')
    op.drop_table('fields')
    op.drop_table('processing_stage_runs')
    op.drop_table('onboarding_sessions')
    op.drop_table('traces')
