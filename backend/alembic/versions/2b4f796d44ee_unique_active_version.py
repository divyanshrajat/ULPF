"""unique_active_version

Revision ID: 2b4f796d44ee
Revises: c0eee8335003
Create Date: 2026-09-10 22:51:44.716381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b4f796d44ee'
down_revision: Union[str, Sequence[str], None] = 'c0eee8335003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_unique_active_rule_version',
        'rule_versions',
        ['rule_id'],
        unique=True,
        sqlite_where=sa.text("status = 'ACTIVE'"),
        postgresql_where=sa.text("status = 'ACTIVE'")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_unique_active_rule_version', table_name='rule_versions')
