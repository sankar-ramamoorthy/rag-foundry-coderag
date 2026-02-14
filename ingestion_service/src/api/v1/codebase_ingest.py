"""
API Endpoints for Repository Ingestion

Provides:
- POST /v1/codebase/ingest-repo: ingest a Git repo or local path
- GET  /v1/codebase/ingest-repo/{ingestion_id}: check ingestion status

Integrates:
- RepoGraphBuilder for code artifact graph construction
- CodebaseGraphPersistence for deterministic node & relationship persistence
- IngestionPipeline for embedding code artifacts
"""

from uuid import uuid4, UUID
import threading
import logging
from pathlib import Path
import tempfile
import shutil

from fastapi import APIRouter, HTTPException, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database_session import get_sessionmaker
from src.core.models import IngestionRequest
from src.core.status_manager import StatusManager
from src.core.codebase.repo_graph_builder import RepoGraphBuilder
from src.core.codebase.codebase_persistence import CodebaseGraphPersistence
from src.core.pipeline import IngestionPipeline

# -----------------------------
# Session and router
# -----------------------------
SessionLocal = get_sessionmaker()
router = APIRouter(tags=["codebase_ingest"])
logger = logging.getLogger(__name__)

# -----------------------------
# Request / Response Models
# -----------------------------
class RepoIngestRequest(BaseModel):
    git_url: str | None = None
    local_path: str | None = None
    provider: str | None = None  # Embedding provider


class RepoIngestResponse(BaseModel):
    ingestion_id: UUID
    status: str


# -----------------------------
# Background ingestion worker
# -----------------------------
def _background_ingest_repo(
    ingestion_id: UUID,
    git_url: str | None,
    local_path: str | None,
    provider: str | None,
):
    """
    Clone or use local repo, build graph, persist nodes & relationships, and embed code artifacts.
    """
    session = SessionLocal()
    StatusManager(session).mark_running(ingestion_id)

    temp_dir = None
    try:
        if git_url:
            import git  # GitPython
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Cloning {git_url} into {temp_dir}")
            git.Repo.clone_from(git_url, temp_dir)
            repo_path = temp_dir
        elif local_path:
            repo_path = str(Path(local_path).resolve())
        else:
            raise ValueError("Either git_url or local_path must be provided")

        # --- Build Repo Graph ---
        builder = RepoGraphBuilder()
        repo_graph = builder.build(repo_path)

        # --- Persist Nodes & Relationships ---
        persistence = CodebaseGraphPersistence(session=session)
        persistence.upsert_nodes(repo_id=str(ingestion_id), nodes=repo_graph.nodes)
        persistence.upsert_relationships(repo_id=str(ingestion_id), relationships=repo_graph.relationships)

        # --- Run embeddings via IngestionPipeline ---
        pipeline = IngestionPipeline()  # Can inject provider/embedder if needed
        for node in repo_graph.nodes:
            text = node.get("text", "")
            if text.strip():
                pipeline.run(text=text, ingestion_id=str(ingestion_id), source_type="code", provider=provider or "ollama")

        StatusManager(session).mark_completed(ingestion_id)
        logger.info(f"✅ Repo ingestion completed: {ingestion_id}")

    except Exception as exc:
        logger.error(f"❌ Repo ingestion failed: {ingestion_id} - {exc}")
        StatusManager(session).mark_failed(ingestion_id, error=str(exc))

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)
        session.close()


# -----------------------------
# POST /v1/codebase/ingest-repo
# -----------------------------
@router.post("/ingest-repo", response_model=RepoIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_repo(
    git_url: str | None = Form(default=None),
    local_path: str | None = Form(default=None),
    provider: str | None = Form(default=None),
) -> RepoIngestResponse:
    if not git_url and not local_path:
        raise HTTPException(status_code=400, detail="Must provide either git_url or local_path")

    ingestion_id = uuid4()
    with SessionLocal() as session:
        StatusManager(session).create_request(
            ingestion_id=ingestion_id,
            source_type="repo",
            metadata={"git_url": git_url, "local_path": local_path, "provider": provider},
        )

    # Fire-and-forget background ingestion
    threading.Thread(
        target=_background_ingest_repo,
        kwargs={
            "ingestion_id": ingestion_id,
            "git_url": git_url,
            "local_path": local_path,
            "provider": provider,
        },
        daemon=True,
    ).start()

    return RepoIngestResponse(ingestion_id=ingestion_id, status="accepted")


# -----------------------------
# GET /v1/codebase/ingest-repo/{ingestion_id}
# -----------------------------
@router.get("/ingest-repo/{ingestion_id}", response_model=RepoIngestResponse)
def get_repo_ingest_status(ingestion_id: str) -> RepoIngestResponse:
    try:
        ingestion_uuid = UUID(ingestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ingestion ID format")

    with SessionLocal() as session:
        request = session.query(IngestionRequest).filter_by(ingestion_id=ingestion_uuid).first()
        if not request:
            raise HTTPException(status_code=404, detail="Ingestion ID not found")

        return RepoIngestResponse(ingestion_id=request.ingestion_id, status=request.status)
