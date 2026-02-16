"""
RepoGraphBuilder

Walk repository, extract Python artifacts, resolve CALLs, extract source text,
and track DEFINES relationships.

MS3-IS6 + MS3-IS4 features:
- Multi-pass CALL resolution
- Scoped resolution (method → class → module → global)
- Tiered confidence scoring (1.0 → 0.8 → 0.5 → 0.0)
- Parent ID attachment
- EXTERNAL handling for unresolved CALLs
- DEFINES relationships for modules/classes
- Artifact text extraction for embeddings (MS4-IS5)
"""

from pathlib import Path
from typing import Optional, Tuple
import ast
import logging

from src.core.codebase.identity import build_global_id
from src.core.extractors.python_extractor import PythonASTExtractor
from src.core.codebase.repo_graph import RepoGraph
from src.core.codebase.symbol_table import build_symbol_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RepoGraphBuilder:
    """
    Walk repository, invoke extractors, collect artifacts,
    resolve CALLs, attach text, and track DEFINES.
    """

    def __init__(self, repo_root: Path, ingestion_id):
        self.repo_root = repo_root
        self.ingestion_id = ingestion_id

    def build(self) -> RepoGraph:
        """Build the repository graph with extraction + text + relationships."""
        graph = RepoGraph(self.repo_root, self.ingestion_id)

        for file_path in self._walk_repo():
            try:
                relative_path = file_path.relative_to(self.repo_root).as_posix()
            except Exception:
                logger.exception(f"[RepoGraphBuilder] Failed to compute relative_path for {file_path}")
                continue

            extractor = self._select_extractor(file_path)
            if extractor is None:
                logger.debug(f"[RepoGraphBuilder] No extractor for {file_path}")
                continue

            try:
                source = file_path.read_text(encoding="utf-8")
            except Exception:
                logger.debug(f"[RepoGraphBuilder] Skipping unreadable file {file_path}")
                continue

            try:
                artifacts = extractor.extract(source)
            except Exception:
                logger.exception(f"[RepoGraphBuilder] Extraction failed for {relative_path}")
                continue

            # Attach text and metadata to each artifact
            for artifact in artifacts:
                artifact["relative_path"] = relative_path
                artifact["ingestion_id"] = self.ingestion_id
                artifact.setdefault("title", artifact.get("name", "Untitled"))
                artifact.setdefault("doc_type", "python source")

                # canonical_id + global_id
                global_id = build_global_id(self.ingestion_id, relative_path, artifact.get("id"))
                artifact["global_id"] = global_id
                artifact["canonical_id"] = global_id[1]

                # Extract artifact text
                artifact["text"] = self._extract_artifact_text(source, artifact)

                logger.debug(
                    f"[RepoGraphBuilder] Adding artifact id={artifact.get('id')} "
                    f"type={artifact.get('artifact_type')} parent={artifact.get('parent_id')} "
                    f"title={artifact.get('title')} global_id={artifact.get('global_id')}"
                )

                artifact["defines"] = []
                graph.add_entity(relative_path, artifact)

        # Build symbol table and attach relationships
        symbol_table = build_symbol_table(graph)
        self._attach_defines(graph)
        self._resolve_calls(graph, symbol_table)

        return graph

    def _extract_artifact_text(self, source: str, artifact: dict) -> str:
        """
        Returns a code snippet corresponding to the artifact:
          - Full file for MODULE
          - AST segment for CLASS, FUNCTION, METHOD
          - Empty string for other types
        """
        artifact_type = artifact.get("artifact_type")

        if artifact_type == "MODULE":
            return source

        # Only extract code segments for types with AST node locations
        if artifact_type in {"CLASS", "FUNCTION", "METHOD"}:
            # Attempt to parse AST and find matching node
            try:
                tree = ast.parse(source)
            except SyntaxError:
                return ""

            lineno = artifact.get("metadata", {}).get("lineno")
            if lineno is None:
                return ""

            # Search for AST node that matches lineno
            for node in ast.walk(tree):
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    if getattr(node, "lineno", None) == lineno:
                        snippet = ast.get_source_segment(source, node)
                        return snippet or ""
        return ""

    # --- (rest of your attachment and CALL resolution logic follows) ---

    def _attach_defines(self, graph: RepoGraph):
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
            if parent_entity:
                parent_entity["defines"].append(child_id)

    def _resolve_calls(self, graph: RepoGraph, symbol_table):
        for call in self._calls(graph):
            name = call.get("name") or ""
            resolution, confidence = self._resolve_in_scope(call, graph)
            if resolution:
                call["resolution"] = resolution
                call["confidence"] = confidence
                continue
            global_res = symbol_table.lookup(name)
            call["resolution"] = global_res if global_res else "EXTERNAL"
            call["confidence"] = 0.5 if global_res else 0.0

    def _calls(self, graph: RepoGraph):
        for entity in graph.all_entities():
            if entity.get("artifact_type") == "CALL":
                yield entity

    def _resolve_in_scope(self, call: dict, graph: RepoGraph) -> Tuple[Optional[str], float]:
        current_parent = call.get("parent_id")
        while current_parent:
            parent_entity = graph.get_entity(current_parent)
            if parent_entity:
                for entity in graph.all_entities():
                    if entity.get("id", "").startswith(current_parent):
                        if entity.get("name") == call.get("name") and entity["artifact_type"] in {
                            "CLASS", "FUNCTION", "METHOD"
                        }:
                            return entity["id"], 1.0
                current_parent = parent_entity.get("parent_id")
            else:
                current_parent = None
        return None, 0.0

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
