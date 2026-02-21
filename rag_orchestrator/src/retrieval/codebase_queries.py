"""
src/retrieval/codebase_queries.py

Graph-aware traversal utilities for codebase artifacts.

This module provides BFS/DFS traversal over canonical artifact graphs,
supporting:
- Directional queries (forward / reverse)
- Relation-type filtering (CALL, DEFINES)
- Depth-limited multi-hop searches
- Deterministic ordering

Author: 
"""

from collections import deque, defaultdict
from typing import List, Set, Dict, Optional
from sqlalchemy.orm import Session
from typing import Dict
#from ingestion_service.models import DocumentNode, DocumentRelationship
from shared.models.base import DocumentNode, DocumentRelationship


class Node:
    """
    Represents a single artifact node in the graph.
    """
    def __init__(self, canonical_id: str, file_path: str, lineno: Optional[int] = None):
        self.canonical_id = canonical_id
        self.file_path = file_path
        self.lineno = lineno
        self.out_edges: Dict[str, Set['Node']] = defaultdict(set)  # relation_type -> set of target nodes
        self.in_edges: Dict[str, Set['Node']] = defaultdict(set)   # relation_type -> set of source nodes

    def __repr__(self):
        return f"Node({self.canonical_id})"


class CodebaseGraph:
    """
    In-memory representation of a codebase's canonical artifact graph.
    """
    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def add_node(self, node: Node):
        self.nodes[node.canonical_id] = node

    def add_edge(self, from_cid: str, to_cid: str, relation_type: str):
        from_node = self.nodes.get(from_cid)
        to_node = self.nodes.get(to_cid)
        if not from_node or not to_node:
            raise ValueError(f"Cannot add edge: nodes missing {from_cid} -> {to_cid}")
        from_node.out_edges[relation_type].add(to_node)
        to_node.in_edges[relation_type].add(from_node)

    def get_node(self, canonical_id: str) -> Optional[Node]:
        return self.nodes.get(canonical_id)


# -------------------------------
# Traversal Utilities
# -------------------------------

def bfs_traversal(
    graph: CodebaseGraph,
    start_cid: str,
    relation_types: Optional[Set[str]] = None,
    direction: str = "forward",
    max_depth: int = 3
) -> List[Node]:
    """
    Breadth-first traversal of graph starting from a node.

    Args:
        graph: CodebaseGraph object
        start_cid: canonical_id to start traversal from
        relation_types: filter edges by type (CALL, DEFINES, etc.)
        direction: 'forward' (out_edges) or 'reverse' (in_edges)
        max_depth: maximum traversal depth

    Returns:
        List of nodes reached during traversal (excluding start node)
    """
    start_node = graph.get_node(start_cid)
    if not start_node:
        return []

    visited: Set[str] = set()
    queue: deque = deque([(start_node, 0)])
    results: List[Node] = []

    while queue:
        current_node, depth = queue.popleft()
        if current_node.canonical_id in visited:
            continue
        visited.add(current_node.canonical_id)

        if depth > 0:
            results.append(current_node)

        if depth >= max_depth:
            continue

        # Choose edges based on direction
        edges = current_node.out_edges if direction == "forward" else current_node.in_edges

        for rel, neighbors in edges.items():
            if relation_types and rel not in relation_types:
                continue
            for neighbor in neighbors:
                if neighbor.canonical_id not in visited:
                    queue.append((neighbor, depth + 1))

    return results


# -------------------------------
# Convenience Traversals
# -------------------------------

def traverse_calls(graph: CodebaseGraph, start_cid: str, depth: int = 3) -> List[Node]:
    """Traverse CALL edges forward."""
    return bfs_traversal(graph, start_cid, relation_types={"CALL"}, direction="forward", max_depth=depth)


def traverse_defines(graph: CodebaseGraph, start_cid: str, depth: int = 3) -> List[Node]:
    """Traverse DEFINES edges forward."""
    return bfs_traversal(graph, start_cid, relation_types={"DEFINES"}, direction="forward", max_depth=depth)


def traverse_incoming_calls(graph: CodebaseGraph, start_cid: str, depth: int = 3) -> List[Node]:
    """Traverse CALL edges in reverse (incoming)."""
    return bfs_traversal(graph, start_cid, relation_types={"CALL"}, direction="reverse", max_depth=depth)


def traverse_incoming_imports(graph: CodebaseGraph, start_cid: str, depth: int = 3) -> List[Node]:
    """Traverse IMPORT edges in reverse (incoming)."""
    return bfs_traversal(graph, start_cid, relation_types={"IMPORT"}, direction="reverse", max_depth=depth)


# -------------------------------
# Graph Loader (Stub)
# -------------------------------



def load_graph_for_repo(repo_id: str, db: Session) -> CodebaseGraph:
    """
    Build an in-memory CodebaseGraph from persisted document_nodes
    and document_relationships for a given repo_id.

    Args:
        repo_id: Repository UUID
        db: SQLAlchemy session

    Returns:
        CodebaseGraph
    """
    graph = CodebaseGraph()

    # ----------------------------
    # 1. Load Nodes
    # ----------------------------
    nodes = (
        db.query(DocumentNode)
        .filter(DocumentNode.repo_id == repo_id)
        .all()
    )

    if not nodes:
        return graph

    # Map DB id -> canonical_id
    id_to_canonical: Dict[str, str] = {}

    for node in nodes:
        new_node = Node(
            canonical_id=node.canonical_id,
            file_path=node.file_path,
            lineno=getattr(node, "lineno", None),
        )
        graph.add_node(new_node)
        id_to_canonical[node.id] = node.canonical_id

    # ----------------------------
    # 2. Load Relationships
    # ----------------------------
    relationships = (
        db.query(DocumentRelationship)
        .filter(DocumentRelationship.from_document_id.in_(id_to_canonical.keys()))
        .all()
    )

    for rel in relationships:
        from_cid = id_to_canonical.get(rel.from_document_id)
        to_cid = id_to_canonical.get(rel.to_document_id)

        if from_cid and to_cid:
            graph.add_edge(
                from_cid,
                to_cid,
                rel.relation_type
            )

    return graph

