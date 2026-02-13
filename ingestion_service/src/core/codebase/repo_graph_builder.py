# ingestion_service/src/core/codebase/repo_graph_builder.py
"""
RepoGraphBuilder

Walk repository, extract Python artifacts, resolve CALLs, and track DEFINES relationships.

MS3-IS6 + MS3-IS4 features:
- Multi-pass CALL resolution
- Scoped resolution (method → class → module → global)
- Tiered confidence scoring (1.0 → 0.8 → 0.5 → 0.0)
- Parent ID attachment
- EXTERNAL handling for unresolved CALLs
- DEFINES relationships for modules/classes
"""

from pathlib import Path
from typing import List, Optional, Dict, Tuple

from src.core.extractors.python_extractor import PythonASTExtractor
from src.core.codebase.repo_graph import RepoGraph
from src.core.codebase.symbol_table import build_symbol_table


class RepoGraphBuilder:
    """
    Walk repository, invoke extractors, collect artifacts,
    resolve CALLs, and track DEFINES.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def build(self) -> RepoGraph:
        """Build the repository graph with DEFINES and CALL resolution."""
        # ----------------------------
        # 1. Build repo graph
        # ----------------------------
        graph = RepoGraph(self.repo_root)

        for file_path in self._walk_repo():
            relative_path = file_path.relative_to(self.repo_root).as_posix()
            extractor = self._select_extractor(file_path)
            if extractor is None:
                continue

            try:
                source = file_path.read_text(encoding="utf-8")
            except Exception:
                continue  # skip unreadable files

            artifacts = extractor.extract(source)
            for artifact in artifacts:
                artifact["defines"] = []
                graph.add_entity(relative_path, artifact)

        # ----------------------------
        # 2. Build symbol table
        # ----------------------------
        symbol_table = build_symbol_table(graph)

        # ----------------------------
        # 3. Attach DEFINES relationships
        # ----------------------------
        self._attach_defines(graph)

        # ----------------------------
        # 4. Resolve CALL artifacts (multi-pass, scoped)
        # ----------------------------
        self._resolve_calls(graph, symbol_table)

        return graph

    # ----------------------------
    # DEFINES Relationship Logic
    # ----------------------------
    def _attach_defines(self, graph: RepoGraph):
        """
        Populate each entity's 'defines' list with canonical IDs
        of entities it directly defines (modules define top-level classes/functions,
        classes define methods/nested classes).
        """
        definition_types = {"CLASS", "FUNCTION", "METHOD"}

        for entity in graph.all_entities():
            artifact_type = entity.get("artifact_type")
            if artifact_type not in definition_types:
                continue

            child_id = entity.get("id")
            parent_id = entity.get("parent_id")
            if not child_id or not parent_id:
                continue

            parent_entity = graph.get_entity(parent_id)
            if parent_entity is None:
                continue

            parent_entity["defines"].append(child_id)

    # ----------------------------
    # CALL Resolution Logic
    # ----------------------------
    def _resolve_calls(self, graph: RepoGraph, symbol_table):
        """
        Resolve CALL artifacts to their likely target definitions and assign a confidence score.

        Multi-pass logic:
        1. Scoped resolution in immediate and parent containers (method → class → module)
           Confidence: 1.0
        2. Global symbol table lookup
           Confidence: 0.5
        3. Unresolved → EXTERNAL
           Confidence: 0.0
        """
        for call in self._calls(graph):
            name = call.get("name")
            if not name:
                call["resolution"] = "EXTERNAL"
                call["confidence"] = 0.0
                continue

            # Multi-pass local + parent scopes
            resolution, confidence = self._resolve_in_scope(call, graph)
            if resolution:
                call["resolution"] = resolution
                call["confidence"] = confidence
                continue

            # Global fallback
            global_res = symbol_table.lookup(name)
            if global_res:
                call["resolution"] = global_res
                call["confidence"] = 0.5
            else:
                call["resolution"] = "EXTERNAL"
                call["confidence"] = 0.0

    def _calls(self, graph: RepoGraph):
        """Yield all CALL artifacts in the graph."""
        for entity in graph.all_entities():
            if entity.get("artifact_type") == "CALL":
                yield entity

    def _resolve_in_scope(self, call: dict, graph: RepoGraph) -> Tuple[Optional[str], float]:
        """
        Attempt to resolve a CALL within its local scope and parent containers.
        Returns (canonical_id, confidence) if found, else (None, 0.0).

        Traversal order:
        1. Method scope (if any)
        2. Class scope (parent)
        3. Module scope
        """
        current_parent = call.get("parent_id")
        while current_parent:
            for entity in graph.all_entities():
                if entity.get("id", "").startswith(current_parent):
                    if entity.get("name") == call.get("name") and entity["artifact_type"] in {"CLASS", "FUNCTION", "METHOD"}:
                        return entity["id"], 1.0
            # Move to parent of current container
            parent_entity = graph.get_entity(current_parent)
            if parent_entity:
                current_parent = parent_entity.get("parent_id")
            else:
                current_parent = None
        return None, 0.0

    # ----------------------------
    # Helpers
    # ----------------------------
    def _walk_repo(self):
        """Walk repository and yield Python files only, skipping hidden directories."""
        for path in self.repo_root.rglob("*.py"):
            if any(part.startswith(".") for part in path.parts):
                continue
            yield path

    def _select_extractor(self, file_path: Path):
        """Return appropriate extractor for the file."""
        if file_path.suffix == ".py":
            rel = file_path.relative_to(self.repo_root).as_posix()
            return PythonASTExtractor(relative_path=rel)
        return None
