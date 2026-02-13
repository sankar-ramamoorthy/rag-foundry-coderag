# ingestion_service/src/core/codebase/repo_graph_builder.py
"""
RepoGraphBuilder

Walk repository, extract Python artifacts, and resolve CALLs.

MS3-IS6 features:
- Multi-pass CALL resolution
- Scoped resolution (module and class)
- Confidence scoring (0.0–1.0)
- Parent ID attachment
- EXTERNAL handling for unresolved CALLs
"""

from pathlib import Path
from typing import List, Optional, Dict, Tuple

from src.core.extractors.python_extractor import PythonASTExtractor
from src.core.codebase.repo_graph import RepoGraph
from src.core.codebase.symbol_table import build_symbol_table


class RepoGraphBuilder:
    """
    Walk repository, invoke extractors, collect artifacts, and resolve CALLs.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def build(self) -> RepoGraph:
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
                # skip unreadable files
                continue

            artifacts = extractor.extract(source)
            for artifact in artifacts:
                graph.add_entity(relative_path, artifact)

        # ----------------------------
        # 2. Build symbol table
        # ----------------------------
        symbol_table = build_symbol_table(graph)

        # ----------------------------
        # 3. Resolve CALL artifacts (multi-pass, scoped)
        # ----------------------------
        self._resolve_calls(graph, symbol_table)

        return graph

    # ----------------------------
    # CALL Resolution Logic
    # ----------------------------
    def _resolve_calls(self, graph: RepoGraph, symbol_table):
        """
        Resolve CALL artifacts with confidence scoring.
        Implements a basic scoped/multi-pass strategy:
        - Local scope (module/class)
        - Global scope via SymbolTable
        """
        # First pass: module/class-local resolution
        for call in self._calls(graph):
            name = call.get("name")
            parent_id = call.get("id")
            call["parent_id"] = parent_id.rsplit("#", 1)[0] if parent_id else None

            # Attempt local scope resolution
            local_res = self._resolve_in_scope(call, graph)
            if local_res:
                call["resolution"], call["confidence"] = local_res
            else:
                # fallback to global symbol table
                global_res = symbol_table.lookup(name) if name else None
                if global_res:
                    call["resolution"] = global_res
                    call["confidence"] = 1.0
                else:
                    call["resolution"] = "EXTERNAL"
                    call["confidence"] = 0.0

    def _calls(self, graph: RepoGraph):
        """Yield all CALL artifacts"""
        for entity in graph.all_entities():
            if entity.get("artifact_type") == "CALL":
                yield entity

    def _resolve_in_scope(self, call: dict, graph: RepoGraph) -> Optional[Tuple[str, float]]:
        """
        Attempt to resolve a CALL within its local scope (module or class).
        Returns (canonical_id, confidence) if found, else None.
        """
        parent = call.get("parent_id")
        if not parent:
            return None

        # Look for definitions inside the same module/class
        for entity in graph.all_entities():
            if entity.get("id", "").startswith(parent):
                if entity.get("name") == call.get("name") and entity["artifact_type"] in {"CLASS", "FUNCTION", "METHOD"}:
                    return entity["id"], 1.0  # strong match

        return None

    # ----------------------------
    # Helpers
    # ----------------------------
    def _walk_repo(self):
        """
        Walk repository and yield Python files only, skipping hidden directories.
        """
        for path in self.repo_root.rglob("*.py"):
            if any(part.startswith(".") for part in path.parts):
                continue
            yield path

    def _select_extractor(self, file_path: Path):
        """
        Return appropriate extractor for the file.
        """
        if file_path.suffix == ".py":
            rel = file_path.relative_to(self.repo_root).as_posix()
            return PythonASTExtractor(relative_path=rel)
        return None
