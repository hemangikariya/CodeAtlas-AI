"""ml

Revision ID: 005_ml
Revises: 004_copilot
Create Date: 2026-08-03 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_ml'
down_revision: Union[str, None] = '004_copilot'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. create trained_models table
    op.create_table(
        'trained_models',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('dataset', sa.String(length=255), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trained_models_model_name', 'trained_models', ['model_name'], unique=False)

    # 2. create prediction_history table
    op.create_table(
        'prediction_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('prediction_type', sa.String(length=100), nullable=False),
        sa.Column('prediction', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prediction_history_repository_id', 'prediction_history', ['repository_id'], unique=False)
    op.create_index('idx_prediction_history_prediction_type', 'prediction_history', ['prediction_type'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_prediction_history_prediction_type', table_name='prediction_history')
    op.drop_index('idx_prediction_history_repository_id', table_name='prediction_history')
    op.drop_table('prediction_history')

    op.drop_index('idx_trained_models_model_name', table_name='trained_models')
    op.drop_table('trained_models')
