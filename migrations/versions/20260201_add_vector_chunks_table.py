"""Add VectorChunks table linked to DocumentNodes

Revision ID: 20260201_chunks
Revises: 20260131_docnodes
Create Date: 2026-02-01
"""

from typing import Sequence, Union
from alembic import op

#revision: str = "20260201_add_vector_chunks_table"
#down_revision: Union[str, Sequence[str], None] = "20260131_add_documentnodes_table"

revision: str = "20260201_chunks"  # 16 chars ✓ (was "20260201_add_vector_chunks_table")
down_revision: Union[str, Sequence[str], None] = "20260131_docnodes"  # Update to match 
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create vector_chunks table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_service.vector_chunks (
            id SERIAL PRIMARY KEY,
            vector vector(768) NOT NULL,
            ingestion_id UUID NOT NULL,
            chunk_id TEXT NOT NULL,
            chunk_index INT NOT NULL,
            chunk_strategy TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            source_metadata JSONB NOT NULL DEFAULT '{}',
            provider TEXT NOT NULL DEFAULT 'ollama',
            document_id UUID REFERENCES ingestion_service.document_nodes(document_id)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion_service.vector_chunks")
