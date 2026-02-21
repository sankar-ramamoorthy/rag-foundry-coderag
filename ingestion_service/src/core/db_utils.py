# ingestion_service/src/core/db_utils.py
"""
Database utilities for ingestion_service.

This module centralizes all database access logic so that:
- API routes remain thin (HTTP only)
- DB logic is reusable and testable
- No duplicate SQL queries exist in endpoints
"""

from typing import Optional, List, Dict
from uuid import UUID
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from .database_session import get_sessionmaker
from .models import IngestionRequest
from shared.models.document_node import DocumentNode

logger = logging.getLogger(__name__)
SessionLocal = get_sessionmaker()


# ==============================================================
# INGESTION HELPERS
# ==============================================================

def create_ingestion_request(
    source_type: str,
    metadata: Dict,
    ingestion_id: Optional[UUID] = None,
) -> UUID:
    """
    Create a new ingestion request row.
    """
    from uuid import uuid4

    if not ingestion_id:
        ingestion_id = uuid4()

    with SessionLocal() as session:
        req = IngestionRequest(
            ingestion_id=ingestion_id,
            source_type=source_type,
            metadata=metadata,
            status="accepted",
        )
        session.add(req)
        session.commit()

        logger.info(f"Created ingestion request {ingestion_id}")

    return ingestion_id


def get_ingestion_status(ingestion_id: UUID) -> Optional[str]:
    """
    Get ingestion status by ID.
    """
    with SessionLocal() as session:
        req = (
            session.query(IngestionRequest)
            .filter_by(ingestion_id=ingestion_id)
            .first()
        )
        return req.status if req else None


# ==============================================================
# REPOSITORY HELPERS
# ==============================================================

def list_complete_repos() -> List[Dict]:
    """
    Return metadata for all repositories with completed ingestions.

    Each dict contains:
        repo_id
        ingestion_id
        status
        created_at
        file_count
        node_count
    """
    with SessionLocal() as session:

        # Get repos with complete ingestion
        repo_rows = (
            session.query(
                DocumentNode.repo_id,
                DocumentNode.ingestion_id,
                IngestionRequest.status,
                IngestionRequest.created_at,
            )
            .join(
                IngestionRequest,
                DocumentNode.ingestion_id == IngestionRequest.ingestion_id,
            )
            .filter(IngestionRequest.status == "complete")
            .group_by(
                DocumentNode.repo_id,
                DocumentNode.ingestion_id,
                IngestionRequest.status,
                IngestionRequest.created_at,
            )
            .all()
        )

        results: List[Dict] = []

        for repo_id, ingestion_id, status, created_at in repo_rows:

            # Count total nodes
            node_count = (
                session.query(func.count(DocumentNode.document_id))
                .filter(DocumentNode.repo_id == repo_id)
                .scalar()
            )

            # Count distinct files
            file_count = (
                session.query(func.count(func.distinct(DocumentNode.relative_path)))
                .filter(DocumentNode.repo_id == repo_id)
                .scalar()
            )

            results.append(
                {
                    "repo_id": repo_id,
                    "ingestion_id": ingestion_id,
                    "status": status,
                    "created_at": created_at,
                    "file_count": int(node_count or 0),
                    "node_count": int(node_count or 0),
                }
            )

        logger.info(f"DB: Found {len(results)} complete repositories")

        return results


# ==============================================================
# GRAPH HELPERS
# ==============================================================

def get_document_nodes_by_canonical_ids(
    repo_id: str,
    canonical_ids: List[str],
) -> List[DocumentNode]:
    """
    Return DocumentNode rows for a repo and list of canonical_ids.
    Used by graph lookup endpoint.
    """
    if not canonical_ids:
        return []

    with SessionLocal() as session:
        nodes = (
            session.query(DocumentNode)
            .filter(
                DocumentNode.repo_id == repo_id,
                DocumentNode.canonical_id.in_(canonical_ids),
            )
            .all()
        )

        logger.info(
            f"DB: {len(nodes)} nodes found for "
            f"{len(canonical_ids)} canonical_ids "
            f"in repo {repo_id[:8]}"
        )

        return nodes