# ingestion_service/src/core/codebase/repo_graph.py
"""
RepoGraph

In-memory representation of a repository graph.

Holds extracted artifacts by canonical ID and file-organized lists of IDs.
"""

from pathlib import Path
from typing import Dict, List


class RepoGraph:
    """
    Stores artifacts for a repository.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.entities: Dict[str, dict] = {}  # canonical_id -> artifact dict
        self.files: Dict[str, List[str]] = {}  # relative_path -> [canonical_id]

    def add_entity(self, relative_path: str, entity: dict):
        """
        Add an artifact to the graph.
        """
        entity_id = entity["id"]
        self.entities[entity_id] = entity
        self.files.setdefault(relative_path, []).append(entity_id)

    def get_entity(self, canonical_id: str) -> dict | None:
        """
        Retrieve an artifact by canonical ID.
        """
        return self.entities.get(canonical_id)

    def all_entities(self) -> list[dict]:
        """
        Return all artifact dictionaries.
        """
        return list(self.entities.values())
