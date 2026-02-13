"""extend document_nodes with artifact_type and repo_id

Revision ID: 20260212_extend_document_nodes_artifact_type_repo
Revises: 20260131_add_documentnodes_table
Create Date: 2026-02-12

"""

from alembic import op

# revision identifiers, used by Alembic.
# revision identifiers, used by Alembic.
revision = "20260212_artifact_repo"  # short, ≤16 chars preferred
down_revision = "20260131_docnodes"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add artifact_type column with default
    op.execute(
        """
        ALTER TABLE document_nodes
        ADD COLUMN artifact_type TEXT NOT NULL DEFAULT 'DOCUMENT';
        """
    )

    # 2. Add repo_id column (no default — mandatory)
    op.execute(
        """
        ALTER TABLE document_nodes
        ADD COLUMN repo_id UUID NOT NULL;
        """
    )

    # 3. Add composite uniqueness constraint
    op.execute(
        """
        ALTER TABLE document_nodes
        ADD CONSTRAINT uq_document_nodes_repo_id_id UNIQUE (repo_id, id);
        """
    )

    # 4. Add indexes for performance
    op.execute(
        """
        CREATE INDEX idx_document_nodes_artifact_type
        ON document_nodes (artifact_type);
        """
    )

    op.execute(
        """
        CREATE INDEX idx_document_nodes_repo_id
        ON document_nodes (repo_id);
        """
    )

    op.execute(
        """
        CREATE INDEX idx_document_nodes_repo_artifact_type
        ON document_nodes (repo_id, artifact_type);
        """
    )


def downgrade():
    # 1. Drop indexes
    op.execute(
        """
        DROP INDEX IF EXISTS idx_document_nodes_repo_artifact_type;
        """
    )
    op.execute(
        """
        DROP INDEX IF EXISTS idx_document_nodes_repo_id;
        """
    )
    op.execute(
        """
        DROP INDEX IF EXISTS idx_document_nodes_artifact_type;
        """
    )

    # 2. Drop uniqueness constraint
    op.execute(
        """
        ALTER TABLE document_nodes
        DROP CONSTRAINT IF EXISTS uq_document_nodes_repo_id_id;
        """
    )

    # 3. Drop columns
    op.execute(
        """
        ALTER TABLE document_nodes
        DROP COLUMN IF EXISTS repo_id;
        """
    )
    op.execute(
        """
        ALTER TABLE document_nodes
        DROP COLUMN IF EXISTS artifact_type;
        """
    )
