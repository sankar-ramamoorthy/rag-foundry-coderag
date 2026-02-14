"""
MS4 Persistence Layer: CodebaseGraphPersistence

Handles saving and retrieving code repository graphs to/from Postgres.
Supports deterministic upserts using repo_id + canonical_id, and manages
document nodes, relationships, and vector links.

Requires:
- SQLAlchemy ORM models: DocumentNode, DocumentRelationship, VectorChunk
- RepoGraphBuilder output nodes and relationships
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from src.core.models_v2.document_node import DocumentNode
from src.core.models_v2.document_relationship import DocumentRelationship
from src.core.models_v2.vector_chunk import VectorChunk
from src.core.database_session import get_sessionmaker
from src.core.codebase.identity import build_canonical_id

logger = logging.getLogger(__name__)
SessionLocal = get_sessionmaker()


class CodebaseGraphPersistence:
    """
    Service for persisting repository graphs into Postgres.
    Ensures deterministic upserts for nodes and relationships.
    """

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session
        self._session = session or SessionLocal()

    # -----------------------------
    # Document Nodes
    # -----------------------------
    def upsert_nodes(self, repo_id: str, nodes: List[dict]) -> None:
        """
        Upsert a list of nodes (functions, classes, modules) into document_nodes.

        Each node dict must include:
        - relative_path: path relative to repo root
        - symbol_path: optional symbol path (for functions/methods)
        - title: display title
        - doc_type: function/class/module
        - source: source file path
        - summary: optional summary
        """
        for node in nodes:
            canonical_id = build_canonical_id(node["relative_path"], node.get("symbol_path"))
            try:
                existing = (
                    self._session.query(DocumentNode)
                    .filter_by(repo_id=repo_id, canonical_id=canonical_id)
                    .first()
                )
                if existing:
                    # Update existing node
                    existing.title = node.get("title", existing.title)
                    existing.summary = node.get("summary", existing.summary)
                    existing.doc_type = node.get("doc_type", existing.doc_type)
                    existing.source = node.get("source", existing.source)
                    logger.debug(f"Updated DocumentNode: {canonical_id}")
                else:
                    # Insert new node
                    new_node = DocumentNode(
                        repo_id=repo_id,
                        canonical_id=canonical_id,
                        title=node["title"],
                        summary=node.get("summary", ""),
                        doc_type=node["doc_type"],
                        source=node["source"],
                    )
                    self._session.add(new_node)
                    logger.debug(f"Inserted DocumentNode: {canonical_id}")
            except SQLAlchemyError as e:
                logger.error(f"Error upserting node {canonical_id}: {e}")
                self._session.rollback()
                raise
        self._session.commit()

    # -----------------------------
    # Document Relationships
    # -----------------------------
    def upsert_relationships(self, repo_id: str, relationships: List[dict]) -> None:
        """
        Upsert relationships between nodes into document_relationships.

        Each relationship dict must include:
        - from_relative_path / from_symbol_path
        - to_relative_path / to_symbol_path
        - relation_type
        - relationship_metadata (optional)
        """
        for rel in relationships:
            from_canonical = build_canonical_id(rel["from_relative_path"], rel.get("from_symbol_path"))
            to_canonical = build_canonical_id(rel["to_relative_path"], rel.get("to_symbol_path"))

            try:
                from_node = (
                    self._session.query(DocumentNode)
                    .filter_by(repo_id=repo_id, canonical_id=from_canonical)
                    .first()
                )
                to_node = (
                    self._session.query(DocumentNode)
                    .filter_by(repo_id=repo_id, canonical_id=to_canonical)
                    .first()
                )
                if not from_node or not to_node:
                    logger.warning(f"Skipping relationship: {from_canonical} -> {to_canonical} (nodes missing)")
                    continue

                # Check if relationship exists
                existing = (
                    self._session.query(DocumentRelationship)
                    .filter_by(
                        from_document_id=from_node.document_id,
                        to_document_id=to_node.document_id,
                        relation_type=rel["relation_type"]
                    )
                    .first()
                )
                if existing:
                    # Update metadata if needed
                    existing.relationship_metadata = rel.get("relationship_metadata", existing.relationship_metadata)
                    logger.debug(f"Updated DocumentRelationship: {from_canonical} -> {to_canonical}")
                else:
                    # Insert new relationship
                    new_rel = DocumentRelationship(
                        from_document_id=from_node.document_id,
                        to_document_id=to_node.document_id,
                        relation_type=rel["relation_type"],
                        relationship_metadata=rel.get("relationship_metadata", {})
                    )
                    self._session.add(new_rel)
                    logger.debug(f"Inserted DocumentRelationship: {from_canonical} -> {to_canonical}")
            except SQLAlchemyError as e:
                logger.error(f"Error upserting relationship {from_canonical} -> {to_canonical}: {e}")
                self._session.rollback()
                raise
        self._session.commit()

    # -----------------------------
    # Retrieval
    # -----------------------------
    def get_node_by_canonical_id(self, repo_id: str, canonical_id: str) -> Optional[DocumentNode]:
        """
        Retrieve a document node by repo_id + canonical_id.
        """
        return (
            self._session.query(DocumentNode)
            .filter_by(repo_id=repo_id, canonical_id=canonical_id)
            .first()
        )

    def close(self):
        """Close the session if created internally."""
        if not self._external_session:
            self._session.close()
