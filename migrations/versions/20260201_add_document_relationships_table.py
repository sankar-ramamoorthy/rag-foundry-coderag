"""Add DocumentRelationship table with unique constraint

Revision ID: 20260201_rels
Revises: 20260201_chunks
Create Date: 2026-02-01
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
#revision = "20260201_add_document_relationships_table"
#down_revision = "20260201_add_vector_chunks_table"

revision = "20260201_rels"  # 12 chars ✓ (was "20260201_add_document_relationships_table")
down_revision = "20260201_chunks"  # Update to match above


branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create document_relationships table with FKs to document_nodes and unique constraint."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_service.document_relationships (
            id SERIAL PRIMARY KEY,
            from_document_id UUID NOT NULL REFERENCES ingestion_service.document_nodes(document_id) ON DELETE CASCADE,
            to_document_id UUID NOT NULL REFERENCES ingestion_service.document_nodes(document_id) ON DELETE CASCADE,
            relation_type TEXT NOT NULL,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT now(),
            CONSTRAINT uq_document_relationship UNIQUE (from_document_id, to_document_id, relation_type)
        )
        """
    )


def downgrade() -> None:
    """Drop document_relationships table."""
    op.execute(
        "DROP TABLE IF EXISTS ingestion_service.document_relationships"
    )
