# ingestion_service/src/core/codebase/repo_graph_builder.py
"""
RepoGraphBuilder

Walk repository, extract Python artifacts, and resolve CALLs.

MS3-IS3 features:
- CALL resolution using SymbolTable
- Confidence scoring (0.0–1.0)
- Parent ID attachment
- EXTERNAL handling for unresolved CALLs
"""

from pathlib import Path
from typing import List, Optional

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
        # 3. Resolve CALL artifacts
        # ----------------------------
        for artifact in graph.all_entities():
            if artifact["artifact_type"] == "CALL":
                call_name: Optional[str] = artifact.get("name")
                if call_name:
                    resolved_id = symbol_table.lookup(call_name)
                    if resolved_id:
                        artifact["resolution"] = resolved_id
                        artifact["confidence"] = 1.0  # strong
                    else:
                        artifact["resolution"] = "EXTERNAL"
                        artifact["confidence"] = 0.0  # weak
                else:
                    artifact["resolution"] = "EXTERNAL"
                    artifact["confidence"] = 0.0

                # Attach parent_id (module or class)
                eid: Optional[str] = artifact.get("id")
                if eid:
                    artifact["parent_id"] = eid.rsplit("#", 1)[0]
                else:
                    artifact["parent_id"] = None

        return graph

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
