"""knowledge layer

Revision ID: 003_knowledge_layer
Revises: 002_repository_indexing
Create Date: 2026-08-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_knowledge_layer'
down_revision: Union[str, None] = '002_repository_indexing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    
    # 1. Enable pgvector extension on PostgreSQL
    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. embeddings table
    # Vector column uses SafeVector fallback: sa.NullType() or VECTOR(384) on Postgres
    if dialect_name == "postgresql":
        from pgvector.sqlalchemy import VECTOR
        vector_col = sa.Column('vector', VECTOR(384), nullable=False)
    else:
        vector_col = sa.Column('vector', sa.Text(), nullable=False)

    op.create_table(
        'embeddings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=False),
        vector_col,
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('embedding_version', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['code_chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_embeddings_chunk_id', 'embeddings', ['chunk_id'], unique=False)

    # Create HNSW index on PostgreSQL for embeddings
    if dialect_name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw "
            "ON embeddings USING hnsw (vector vector_cosine_ops)"
        )

    # 3. graph_nodes table
    op.create_table(
        'graph_nodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_graph_nodes_snapshot_id', 'graph_nodes', ['snapshot_id'], unique=False)

    # 4. graph_edges table
    op.create_table(
        'graph_edges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('source_node_id', sa.UUID(), nullable=False),
        sa.Column('target_node_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_node_id'], ['graph_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_node_id'], ['graph_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_graph_edges_snapshot_id', 'graph_edges', ['snapshot_id'], unique=False)
    op.create_index('idx_graph_edges_source_node_id', 'graph_edges', ['source_node_id'], unique=False)
    op.create_index('idx_graph_edges_target_node_id', 'graph_edges', ['target_node_id'], unique=False)

    # 5. retrieval_cache table
    op.create_table(
        'retrieval_cache',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('embedding_hash', sa.String(length=64), nullable=False),
        sa.Column('snapshot_id', sa.UUID(), nullable=False),
        sa.Column('retrieved_node_ids', sa.JSON(), nullable=False),
        sa.Column('context', sa.Text(), nullable=False),
        sa.Column('ttl', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_retrieval_cache_query_hash', 'retrieval_cache', ['query_hash'], unique=False)
    op.create_index('idx_retrieval_cache_snapshot_id', 'retrieval_cache', ['snapshot_id'], unique=False)

def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    
    op.drop_index('idx_retrieval_cache_snapshot_id', table_name='retrieval_cache')
    op.drop_index('idx_retrieval_cache_query_hash', table_name='retrieval_cache')
    op.drop_table('retrieval_cache')
    
    op.drop_index('idx_graph_edges_target_node_id', table_name='graph_edges')
    op.drop_index('idx_graph_edges_source_node_id', table_name='graph_edges')
    op.drop_index('idx_graph_edges_snapshot_id', table_name='graph_edges')
    op.drop_table('graph_edges')
    
    op.drop_index('idx_graph_nodes_snapshot_id', table_name='graph_nodes')
    op.drop_table('graph_nodes')
    
    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_embeddings_vector_hnsw")
    op.drop_index('idx_embeddings_chunk_id', table_name='embeddings')
    op.drop_table('embeddings')
    
    if dialect_name == "postgresql":
        op.execute("DROP EXTENSION IF EXISTS vector")
