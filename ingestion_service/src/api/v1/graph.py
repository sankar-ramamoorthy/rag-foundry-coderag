# ingestion_service/src/api/v1/graph.py

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
import logging

from ingestion_service.src.core import db_utils

router = APIRouter(prefix="/graph", tags=["graph"])
logger = logging.getLogger(__name__)


class GraphNode(BaseModel):
    document_id: str
    canonical_id: str
    relative_path: str
    title: str
    doc_type: str


class CanonicalLookupResponse(BaseModel):
    nodes: List[GraphNode]
    total: int


@router.get("/repos/{repo_id}/nodes", response_model=CanonicalLookupResponse)
async def get_nodes_by_canonical_ids(
    repo_id: str,
    canonical_ids: str = Query(..., description="Comma-separated canonical_ids"),
):
    """
    Convert canonical_ids → document_ids for graph traversal.

    Example:
    /v1/graph/repos/<repo_id>/nodes?canonical_ids=file.py,file.py#function
    """

    if not canonical_ids.strip():
        raise HTTPException(400, "canonical_ids required")

    cids = [cid.strip() for cid in canonical_ids.split(",") if cid.strip()]
    if not cids:
        return CanonicalLookupResponse(nodes=[], total=0)

    logger.debug(f"Graph lookup: repo={repo_id[:8]}, cids={len(cids)}")

    # 🔥 DB call centralized here
    nodes = db_utils.get_document_nodes_by_canonical_ids(repo_id, cids)

    result = [
        GraphNode(
            document_id=node.document_id,
            canonical_id=node.canonical_id,
            relative_path=node.relative_path,
            title=node.title,
            doc_type=node.doc_type,
        )
        for node in nodes
    ]

    logger.info(
        f"Graph lookup: {len(cids)} canonical_ids → {len(result)} nodes"
    )

    return CanonicalLookupResponse(
        nodes=result,
        total=len(result),
    )