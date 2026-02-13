# ingestion_service/src/core/models_v2/document_node.py
"""
ORM model for DocumentNodes table using pgvector.
Includes bidirectional relationships to DocumentRelationship.
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.core.models import Base
import uuid
import logging
from pgvector.sqlalchemy import Vector  # pgvector type

if TYPE_CHECKING:
    from .vector_chunk import VectorChunk
    from .document_relationship import DocumentRelationship

logger = logging.getLogger(__name__)
class DocumentNode(Base):
    """
    Represents a logical document, the unit of retrieval for structured RAG.

    Attributes:
        document_id: Primary key UUID.
        title: Document title.
        summary: Text summary of the document.
        summary_embedding: 768-dimensional embedding vector (pgvector).
        source: Source name or URI.
        ingestion_id: Foreign key to the ingestion request.
        doc_type: Type/category of the document.
        vector_chunks: List of related VectorChunks.
        outgoing_relationships: List of DocumentRelationship where this node is the source.
        incoming_relationships: List of DocumentRelationship where this node is the target.
    """
    __tablename__ = "document_nodes"
    __table_args__ = {"schema": "ingestion_service"}
    logger.debug("DocumentNode Represents a logical document, the unit of retrieval for structured RAG.")

    document_id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: str = Column(String, nullable=False)
    summary: str = Column(Text, nullable=False)
    summary_embedding: list[float] = Column(Vector(768), nullable=True)  # pgvector
    source: str = Column(String, nullable=False)
    ingestion_id: str = Column(String, ForeignKey("ingestion_service.ingestion_requests.ingestion_id"), nullable=False)
    doc_type: str = Column(String, nullable=False)

    # Relationship to VectorChunks
    vector_chunks: "list[VectorChunk]" = relationship("VectorChunk", back_populates="document_node")

    # -----------------------------
    # Relationships to DocumentRelationship
    # -----------------------------
    outgoing_relationships: "list[DocumentRelationship]" = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.from_document_id",
        back_populates="from_node",
        cascade="all, delete-orphan",
    )

    incoming_relationships: "list[DocumentRelationship]" = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.to_document_id",
        back_populates="to_node",
        cascade="all, delete-orphan",
    )
