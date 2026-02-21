# rag_orchestrator/src/retrieval/codebase_utils.py
"""
Utilities for hybrid vector+graph retrieval.
"""
from typing import Set, Dict, Optional, List

from functools import lru_cache
import logging


from .codebase_queries import CodebaseGraph, load_graph_for_repo
from .types import RetrievedChunk

logger = logging.getLogger(__name__)

# Global graph cache (single repo for M1)
_repo_graphs: Dict[str, CodebaseGraph] = {}

def canonical_ids_to_document_ids(
    repo_id: str, 
    canonical_ids: Set[str], 
    db: Session
) -> Set[str]:
    """
    Convert canonical_ids → document_ids for a repo.
    
    >>> canonical_ids_to_document_ids("repo1", {"math_utils.py"}, db)
    {"doc-uuid-1", "doc-uuid-2"}
    """
    if not canonical_ids:
        return set()
    
    document_ids = {
        node.document_id 
        for node in db.query(DocumentNode)
        .filter(DocumentNode.repo_id == repo_id)
        .filter(DocumentNode.canonical_id.in_(canonical_ids))
        .all()
    }
    logger.debug(f"Resolved {len(canonical_ids)} canonical_ids → {len(document_ids)} document_ids")
    return document_ids

def get_cached_graph(repo_id: str, db: Session, force_reload: bool = False) -> CodebaseGraph:
    """
    Get CodebaseGraph for repo_id (in-memory cached).
    """
    global _repo_graphs
    
    if force_reload or repo_id not in _repo_graphs:
        logger.info(f"Loading graph for repo_id={repo_id[:8]}...")
        _repo_graphs[repo_id] = load_graph_for_repo(repo_id, db)
        logger.info(f"Graph loaded: {len(_repo_graphs[repo_id].nodes)} nodes")
    
    return _repo_graphs[repo_id]


