from pathlib import Path
from typing import Dict, List, Optional

from core.extractors.python_extractor import PythonASTExtractor


class RepoGraph:
    """
    In-memory representation of a repository graph.

    Holds extracted artifacts by canonical ID and file-organized lists of IDs.
    Also maintains CALLS and DEFINES relationships.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.entities: Dict[str, dict] = {}  # canonical_id -> artifact dict
        self.files: Dict[str, List[str]] = {}  # relative_path -> [canonical_id]

    def add_entity(self, relative_path: str, entity: dict):
        entity_id = entity["id"]
        self.entities[entity_id] = entity
        self.files.setdefault(relative_path, []).append(entity_id)

    def get_entity(self, entity_id: str) -> Optional[dict]:
        return self.entities.get(entity_id)

    def all_entities(self) -> List[dict]:
        return list(self.entities.values())


class RepoGraphBuilder:
    """
    Walk repository, invoke extractors, collect artifacts,
    and perform layered resolution for CALLS and DEFINES relationships.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.graph: Optional[RepoGraph] = None
        self.global_symbol_index: Dict[str, str] = {}  # name -> canonical_id

    def build(self) -> RepoGraph:
        """
        Build the repo graph by walking files, extracting artifacts,
        and performing second-pass resolution.
        """
        self.graph = RepoGraph(self.repo_root)

        # Phase 1: Extraction
        for file_path in self._walk_repo():
            relative_path = file_path.relative_to(self.repo_root).as_posix()
            extractor = self._select_extractor(file_path)
            if extractor is None:
                continue

            try:
                source = file_path.read_text(encoding="utf-8")
            except Exception:
                # Could log a warning here
                continue

            artifacts = extractor.extract(source)

            for artifact in artifacts:
                self.graph.add_entity(relative_path, artifact)

        # Phase 2: Build global symbol index
        self._build_global_symbol_index()

        # Phase 3: Resolve CALLS
        self._resolve_calls()

        # Phase 4: Establish DEFINES relationships
        self._establish_defines()

        return self.graph

    def _walk_repo(self):
        """
        Walk repository and yield Python files only.
        """
        for path in self.repo_root.rglob("*.py"):
            if any(part.startswith(".") for part in path.parts):
                continue
            yield path

    def _select_extractor(self, file_path: Path):
        """
        Return an extractor for the file, or None if unsupported.
        """
        if file_path.suffix == ".py":
            rel = file_path.relative_to(self.repo_root).as_posix()
            return PythonASTExtractor(relative_path=rel)
        return None

    def _build_global_symbol_index(self):
        """
        Build a simple global symbol index mapping names to canonical IDs.
        Only considers MODULE, CLASS, FUNCTION/METHOD artifacts.
        """
        assert self.graph is not None
        for entity in self.graph.all_entities():
            if entity["artifact_type"] in {"MODULE", "CLASS", "METHOD", "FUNCTION"}:
                self.global_symbol_index[entity["name"]] = entity["id"]

    def _resolve_calls(self):
        """
        Link CALL artifacts to their targets using parent_id and global symbol index.
        """
        assert self.graph is not None
        for entity in self.graph.all_entities():
            if entity["artifact_type"] != "CALL":
                continue

            target_name = entity["name"]
            # Attempt to resolve via global symbol index
            resolved_id = self.global_symbol_index.get(target_name, "EXTERNAL")
            entity["resolution"] = resolved_id

    def _establish_defines(self):
        """
        Populate DEFINES relationships for:
        - MODULE -> CLASS
        - MODULE -> FUNCTION
        - CLASS  -> METHOD
        """
        assert self.graph is not None

        for entity in self.graph.all_entities():
            parent_id = entity.get("parent_id")
            if not parent_id:
                continue

            parent_entity = self.graph.get_entity(parent_id)
            if not parent_entity:
                continue

            parent_type = parent_entity["artifact_type"]
            child_type = entity["artifact_type"]

            # MODULE defines CLASS or FUNCTION
            if parent_type == "MODULE" and child_type in {"CLASS", "FUNCTION"}:
                defines = parent_entity.setdefault("defines", [])
                if entity["id"] not in defines:
                    defines.append(entity["id"])

            # CLASS defines METHOD
            elif parent_type == "CLASS" and child_type == "METHOD":
                defines = parent_entity.setdefault("defines", [])
                if entity["id"] not in defines:
                    defines.append(entity["id"])


