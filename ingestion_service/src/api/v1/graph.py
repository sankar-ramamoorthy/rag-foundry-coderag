# ingestion_service/src/api/v1/graph.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
import logging

from src.core import db_utils

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

    # Use the existing DB utility
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

    return CanonicalLookupResponse(nodes=result, total=len(result))

@router.get("/repos/{repo_id}", response_model=CanonicalLookupResponse)
async def get_full_graph(
    repo_id: str,
):
    """
    Export the entire graph (nodes and edges) for the given repository.

    Example:
    /v1/graph/repos/<repo_id>
    """
    
    logger.debug(f"Graph export: repo={repo_id[:8]}")

    # 🔥 Fetch the full graph for the repo (nodes and relationships)
    graph = db_utils.get_full_graph_for_repo(repo_id)

    # Convert nodes to the GraphNode format
    nodes = [
        GraphNode(
            document_id=node.document_id,
            canonical_id=node.canonical_id,
            relative_path=node.relative_path,
            title=node.title,
            doc_type=node.doc_type,
        )
        for node in graph.nodes
    ]
    
    # Convert edges to the format {from, to, relation_type}
    edges = [
        {"from": edge[0], "to": edge[1], "relation_type": edge[2]}
        for edge in graph.edges
    ]

    logger.info(f"Graph export: repo={repo_id[:8]} - {len(nodes)} nodes, {len(edges)} edges")

    return {"nodes": nodes, "edges": edges}

# ingestion_service/src/api/v1/graph.py

@router.get("/repos/{repo_id}", response_model=CanonicalLookupResponse)
async def get_full_graph(
    repo_id: str,
):
    """
    Export the entire graph (nodes and edges) for the given repository.

    Example:
    /v1/graph/repos/<repo_id>
    """
    
    logger.debug(f"Graph export: repo={repo_id[:8]}")

    # 🔥 Fetch the full graph for the repo (nodes and relationships)
    graph = db_utils.get_full_graph_for_repo(repo_id)

    # Convert nodes to the GraphNode format
    nodes = [
        GraphNode(
            document_id=node.document_id,
            canonical_id=node.canonical_id,
            relative_path=node.relative_path,
            title=node.title,
            doc_type=node.doc_type,
        )
        for node in graph[0]  # first element: nodes
    ]
    
    # Convert edges to the format {from, to, relation_type}
    edges = [
        {"from": edge[0], "to": edge[1], "relation_type": edge[2]}
        for edge in graph[1]  # second element: edges
    ]

    logger.info(f"Graph export: repo={repo_id[:8]} - {len(nodes)} nodes, {len(edges)} edges")

    return {"nodes": nodes, "edges": edges}    