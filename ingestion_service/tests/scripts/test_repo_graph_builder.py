from pathlib import Path
from ingestion_service.src.core.codebase.repo_graph_builder import RepoGraphBuilder
import pytest
# --- CONFIGURE YOUR TEST REPO PATH ---
# For testing, you can point this to a small folder with a few Python files.
# Here we’ll use the current src/ folder as a lightweight example.
repo_path = Path(__file__).parent.parent / "src"
print("Scanning repo at:", repo_path,"Path(__file__)",Path(__file__))

# Correct path to the actual source folder
repo_path = Path(__file__).resolve().parent.parent.parent / "src"
print("Scanning repo at:", repo_path)

# --- BUILD THE GRAPH ---
builder = RepoGraphBuilder(repo_path)
graph = builder.build()

# --- SIMPLE PRINTOUT OF RESULTS ---
print("\n=== FILES AND ARTIFACT IDS ===")
for file, ids in graph.files.items():
    print(f"{file}: {len(ids)} artifacts")
    for eid in ids:
        entity = graph.get_entity(eid)
        print(f"  - {entity['artifact_type']} {entity['name']}")

print("\n=== CALL RESOLUTIONS ===")
for entity in graph.all_entities():
    if entity["artifact_type"] == "CALL":
        print(f"{entity['name']} --> {entity.get('resolution')} (parent: {entity.get('parent_id')})")

print("\n=== DEFINES RELATIONSHIPS ===")
for entity in graph.all_entities():
    defines = entity.get("defines")
    if defines:
        print(f"{entity['name']} DEFINES: {[graph.get_entity(cid)['name'] for cid in defines]}")

print("\n=== TOTAL ARTIFACTS ===", len(graph.all_entities()))
