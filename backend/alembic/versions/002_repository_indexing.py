"""repository indexing

Revision ID: 002_repository_indexing
Revises: 001_initial
Create Date: 2026-07-31 12:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_repository_indexing'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. repositories table
    op.create_table(
        'repositories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_repositories_project_id', 'repositories', ['project_id'])

    # 2. repository_snapshots table
    op.create_table(
        'repository_snapshots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('branch', sa.String(length=255), nullable=True),
        sa.Column('commit_sha', sa.String(length=100), nullable=True),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('upload_time', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_snapshots_repository_id', 'repository_snapshots', ['repository_id'])

    # 3. folders table
    op.create_table(
        'folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('parent_folder_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=1024), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_folder_id'], ['folders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_folders_snapshot_id', 'folders', ['snapshot_id'])

    # 4. files table
    op.create_table(
        'files',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('folder_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=1024), nullable=False),
        sa.Column('content_chunk', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_files_snapshot_id', 'files', ['snapshot_id'])
    op.create_index('idx_files_folder_id', 'files', ['folder_id'])

    # 5. code_chunks table
    op.create_table(
        'code_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_code_chunks_file_id', 'code_chunks', ['file_id'])

    # 6. dependencies table
    op.create_table(
        'dependencies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('source', sa.String(length=1024), nullable=False),
        sa.Column('target', sa.String(length=1024), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dependencies_snapshot_id', 'dependencies', ['snapshot_id'])

    # 7. detected_languages table
    op.create_table(
        'detected_languages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('language', sa.String(length=100), nullable=False),
        sa.Column('file_count', sa.Integer(), nullable=False),
        sa.Column('line_count', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_detected_languages_snapshot_id', 'detected_languages', ['snapshot_id'])

def downgrade() -> None:
    op.drop_table('detected_languages')
    op.drop_table('dependencies')
    op.drop_table('code_chunks')
    op.drop_table('files')
    op.drop_table('folders')
    op.drop_table('repository_snapshots')
    op.drop_table('repositories')
