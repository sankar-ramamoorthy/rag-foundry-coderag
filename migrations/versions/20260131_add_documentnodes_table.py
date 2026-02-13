"""Add DocumentNodes table using pgvector (with summary embedding)

Revision ID: 20260131_docnodes
Revises: 20251229_vectors
Create Date: 2026-01-31
"""

from alembic import op
#import sqlalchemy as sa
#from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
#revision = "20260131_add_documentnodes_table"
#down_revision = "20251229_add_vectors_table"

revision = "20260131_docnodes"  # 16 chars ✓ (was "20260131_add_documentnodes_table")
down_revision = "20251229_vectors"  # Update to match above

branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create DocumentNodes table with 768-dim pgvector embeddings."""
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_service.document_nodes (
            document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            summary_embedding vector(768),
            source TEXT NOT NULL,
            ingestion_id UUID NOT NULL REFERENCES ingestion_service.ingestion_requests(ingestion_id),
            doc_type TEXT NOT NULL
        )
        """
    )


def downgrade() -> None:
    """Drop DocumentNodes table."""
    op.execute("DROP TABLE IF EXISTS ingestion_service.document_nodes")
