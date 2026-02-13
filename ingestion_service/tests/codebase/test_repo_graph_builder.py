# ingestion_service/tests/scripts/test_repo_graph_builder.py
import pytest
from pathlib import Path

from src.core.codebase.repo_graph_builder import RepoGraphBuilder
from src.core.codebase.symbol_table import build_symbol_table


@pytest.fixture(scope="module")
def repo_graph():
    """
    Build the repo graph once for the whole test module.
    """
    # Adjust path if needed; here we use the `src` folder in the repo root
    repo_root = Path(__file__).resolve().parent.parent.parent / "src"
    builder = RepoGraphBuilder(repo_root)
    return builder.build()


@pytest.fixture(scope="module")
def symbol_table(repo_graph):
    """
    Build the symbol table from the repo graph.
    """
    return build_symbol_table(repo_graph)


def test_total_artifacts(repo_graph):
    """
    Ensure some artifacts were collected.
    """
    assert len(repo_graph.entities) > 0, "No artifacts were collected"


def test_some_calls_resolved(repo_graph, symbol_table):
    """
    Check that CALL artifacts have resolution and parent_id.
    """
    calls = [a for a in repo_graph.all_entities() if a["artifact_type"] == "CALL"]
    assert calls, "No CALL artifacts found"

    for call in calls[:20]:  # check a sample of 20
        name = call.get("name")
        resolution = call.get("resolution")
        parent = call.get("parent_id")

        assert parent is not None, f"CALL '{name}' has no parent_id"

        # Resolution should either be EXTERNAL or a known canonical ID
        if resolution != "EXTERNAL":
            assert resolution in repo_graph.entities or resolution in symbol_table.all_symbols(), (
                f"CALL '{name}' resolves to unknown ID '{resolution}'"
            )


def test_modules_and_classes_collected(repo_graph):
    """
    Ensure modules and classes were extracted.
    """
    modules = [a for a in repo_graph.all_entities() if a["artifact_type"] == "MODULE"]
    classes = [a for a in repo_graph.all_entities() if a["artifact_type"] == "CLASS"]

    assert modules, "No MODULE artifacts collected"
    assert classes, "No CLASS artifacts collected"


def test_functions_and_methods_collected(repo_graph):
    """
    Ensure functions and methods were extracted.
    """
    funcs = [a for a in repo_graph.all_entities() if a["artifact_type"] in ("FUNCTION", "METHOD")]
    assert funcs, "No FUNCTION or METHOD artifacts collected"


def test_imports_collected(repo_graph):
    """
    Ensure import statements were extracted.
    """
    imports = [a for a in repo_graph.all_entities() if a["artifact_type"] == "IMPORT"]
    assert imports, "No IMPORT artifacts collected"
