"""copilot

Revision ID: 004_copilot
Revises: 003_knowledge_layer
Create Date: 2026-08-03 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_copilot'
down_revision: Union[str, None] = '003_knowledge_layer'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'generated_artifacts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('artifact_type', sa.String(length=100), nullable=False),
        sa.Column('generator', sa.String(length=100), nullable=False),
        sa.Column('artifact_version', sa.String(length=50), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=False),
        sa.Column('llm_provider', sa.String(length=100), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_generated_artifacts_repository_id', 'generated_artifacts', ['repository_id'], unique=False)
    op.create_index('idx_generated_artifacts_snapshot_id', 'generated_artifacts', ['snapshot_id'], unique=False)
    op.create_index('idx_generated_artifacts_artifact_type', 'generated_artifacts', ['artifact_type'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_generated_artifacts_artifact_type', table_name='generated_artifacts')
    op.drop_index('idx_generated_artifacts_snapshot_id', table_name='generated_artifacts')
    op.drop_index('idx_generated_artifacts_repository_id', table_name='generated_artifacts')
    op.drop_table('generated_artifacts')
