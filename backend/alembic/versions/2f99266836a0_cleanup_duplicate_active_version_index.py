"""cleanup_duplicate_active_version_index

Revision ID: 2f99266836a0
Revises: 10b99c88f819
Create Date: 2026-09-13 15:49:46.488360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f99266836a0'
down_revision: Union[str, Sequence[str], None] = '10b99c88f819'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    indexes = insp.get_indexes('rule_versions')
    if any(ix['name'] == 'ix_unique_active_rule_version' for ix in indexes):
        op.drop_index('ix_unique_active_rule_version', table_name='rule_versions')

def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    indexes = insp.get_indexes('rule_versions')
    if not any(ix['name'] == 'ix_unique_active_rule_version' for ix in indexes):
        op.create_index(
            'ix_unique_active_rule_version',
            'rule_versions',
            ['rule_id'],
            unique=True,
            sqlite_where=sa.text("status = 'ACTIVE'"),
            postgresql_where=sa.text("status = 'ACTIVE'")
        )
