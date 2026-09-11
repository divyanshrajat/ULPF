"""rule_lock_adaptive_counters

Revision ID: a1b2c3d4e5f6
Revises: 2b4f796d44ee
Create Date: 2026-09-11 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '2b4f796d44ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add adaptive spot-check counters to rule_locks."""
    op.add_column('rule_locks', sa.Column('events_since_lock', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('rule_locks', sa.Column('events_since_mismatch', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove adaptive spot-check counters from rule_locks."""
    op.drop_column('rule_locks', 'events_since_mismatch')
    op.drop_column('rule_locks', 'events_since_lock')
