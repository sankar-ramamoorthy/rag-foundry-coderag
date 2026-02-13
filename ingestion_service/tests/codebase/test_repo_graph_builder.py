from pathlib import Path
import pytest
from ingestion_service.src.core.codebase.repo_graph_builder import RepoGraphBuilder


def test_repo_graph_builder_basic(tmp_path):
    p = tmp_path / "one.py"
    p.write_text("def foo():\n    pass\n")

    builder = RepoGraphBuilder(tmp_path)
    graph = builder.build()

    # One module + one function
    assert any("one.py" in x for x in graph.files)
    assert len(graph.entities) == 2

    # Keys include module and function IDs
    ids = list(graph.entities.keys())
    assert tmp_path.joinpath("one.py").relative_to(tmp_path).as_posix() in ids
    assert any("#foo" in i for i in ids)
