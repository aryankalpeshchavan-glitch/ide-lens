"""add ownership, heartbeat, and retry tracking

Revision ID: c948172dfa01
Revises: b879365f4cac
Create Date: 2026-09-06 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c948172dfa01'
down_revision: Union[str, Sequence[str], None] = 'b879365f4cac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add owner_id, last_heartbeat_at, retry_count to research_runs
    op.add_column('research_runs', sa.Column('owner_id', sa.String(length=128), nullable=True))
    op.create_index(op.f('ix_research_runs_owner_id'), 'research_runs', ['owner_id'], unique=False)
    op.add_column('research_runs', sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('research_runs', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))

    # Add owner_id to documents
    op.add_column('documents', sa.Column('owner_id', sa.String(length=128), nullable=True))
    op.create_index(op.f('ix_documents_owner_id'), 'documents', ['owner_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_owner_id'), table_name='documents')
    op.drop_column('documents', 'owner_id')
    op.drop_column('research_runs', 'retry_count')
    op.drop_column('research_runs', 'last_heartbeat_at')
    op.drop_index(op.f('ix_research_runs_owner_id'), table_name='research_runs')
    op.drop_column('research_runs', 'owner_id')
