# ingestion_service/src/core/crud/crud_document_node.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.models_v2.document_node import DocumentNode


def create_document_node(
    session: Session,
    *,
    document_id: UUID,
    title: str,
    summary: str,
    source: str,
    ingestion_id: UUID,
    doc_type: str,
) -> DocumentNode:
    """
    Create and persist a new DocumentNode.

    This function does NOT create sessions or engines.
    """
    node = DocumentNode(
        document_id=document_id,
        title=title,
        summary=summary,
        source=source,
        ingestion_id=ingestion_id,
        doc_type=doc_type,
    )

    session.add(node)
    session.commit()
    session.refresh(node)

    return node


def get_document_node(
    session: Session,
    document_id: UUID,
) -> Optional[DocumentNode]:
    """
    Retrieve a DocumentNode by its ID.
    """
    return (
        session.query(DocumentNode)
        .filter(DocumentNode.document_id == document_id)
        .one_or_none()
    )


def list_document_nodes_by_ingestion(
    session: Session,
    ingestion_id: UUID,
) -> List[DocumentNode]:
    """
    List all DocumentNodes produced by a given ingestion request.
    """
    return (
        session.query(DocumentNode)
        .filter(DocumentNode.ingestion_id == ingestion_id)
        .order_by(DocumentNode.document_id)
        .all()
    )
def update_document_node_summary(
    session, ingestion_id: UUID, summary: str
) -> bool:
    """MS7-IS3: Update document_node.summary by ingestion_id."""
    
    doc = (session.query(DocumentNode)
           .filter_by(ingestion_id=ingestion_id)
           .first())
    
    if doc:
        doc.summary = summary
        session.commit()
        return True
    return False
