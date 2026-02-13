import logging
from typing import List, Optional, Callable, Dict, Any, cast

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from src.core.config import get_settings
from shared.embedders.query import embed_query
from shared.embedders.factory import get_embedder

from shared.retrieval.retrieval_plan import RetrievalPlan
from rag_orchestrator.src.retrieval.execute_plan import execute_retrieval_plan
from rag_orchestrator.src.retrieval.agent_adapter import prepare_chunks_for_agent
from rag_orchestrator.src.retrieval.types import RetrievedChunk

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AgentChunk(Dict):
    text: str
    document_id: str
    chunk_id: str
    score: Optional[float]
    metadata: Dict[str, Any]


# ------------------------------------------------------------------
# Response models
# ------------------------------------------------------------------

class RAGResult(BaseModel):
    answer: str
    sources: List[str]


class SearchResultItem(BaseModel):
    text: str
    source: Optional[str] = "N/A"


# ------------------------------------------------------------------
# Full RAG pipeline
# ------------------------------------------------------------------

async def run_rag(
    query: str,
    *,
    top_k: int = 20,
    max_chunks_per_doc: int = 5,
    max_total_tokens: int = 2048,
    provider: str | None = None,
    model: str | None = None,
    chunk_filter_fn: Optional[Callable[[RetrievedChunk], bool]] = None,
) -> RAGResult:

    settings = get_settings()

    # --------------------------------------------------------------
    # Step 1: Embed query
    # --------------------------------------------------------------
    embedder = get_embedder(
        provider=settings.EMBEDDING_PROVIDER,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_model=settings.OLLAMA_EMBED_MODEL,
        ollama_batch_size=settings.OLLAMA_BATCH_SIZE,
    )
    query_embedding = embed_query(query, embedder)

    # --------------------------------------------------------------
    # Step 2: Global chunk search via HTTP
    # --------------------------------------------------------------
    search_url = f"{settings.VECTOR_STORE_URL}/v1/vectors/search"
    payload = {"query_vector": query_embedding, "k": top_k}

    async with httpx.AsyncClient( timeout=120) as client:
        try:
            resp = await client.post(search_url, json=payload)
            resp.raise_for_status()
            raw_results = resp.json().get("results", [])
        except Exception as e:
            logger.error("Vector search failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    # --------------------------------------------------------------
    # Step 3: Infer seed documents (deterministic)
    # --------------------------------------------------------------
    seed_document_ids: List[str] = []
    seen = set()

    retrieved_chunks_by_document: Dict[str, List[RetrievedChunk]] = {}

    for r in raw_results:
        doc_id = r.get("document_id") or r.get("metadata", {}).get("document_id")
        if not doc_id:
            continue

        # Track seed documents
        if doc_id not in seen:
            seen.add(doc_id)
            seed_document_ids.append(doc_id)

        # Convert to RetrievedChunk
        chunk = RetrievedChunk(
            document_id=doc_id,
            chunk_id=r["chunk_id"],
            text=r["text"],
            score=r.get("score"),
            metadata=r.get("metadata", {}),
        )
        retrieved_chunks_by_document.setdefault(doc_id, []).append(chunk)

    logger.info("Inferred %d seed documents", len(seed_document_ids))

    # --------------------------------------------------------------
    # Step 4: Build RetrievalPlan
    # --------------------------------------------------------------
    plan = RetrievalPlan(
        seed_document_ids=set(seed_document_ids),
        expanded_document_ids=set(),
        expansion_metadata={},
    )

    # --------------------------------------------------------------
    # Step 5: Execute RetrievalPlan
    # --------------------------------------------------------------
    retrieved_context = execute_retrieval_plan(
        plan=plan,
        retrieved_chunks_by_document=retrieved_chunks_by_document,
        debug=True,
    )

    # --------------------------------------------------------------
    # Step 6: Prepare chunks for agent
    # --------------------------------------------------------------
    agent_chunks_raw = prepare_chunks_for_agent(
        retrieved_context,
        document_order=seed_document_ids,
        max_chunks_per_doc=max_chunks_per_doc,
        max_total_chunks=9999,
        filter_chunk=chunk_filter_fn,
        debug=True,
    )

    agent_chunks: List[AgentChunk] = [cast(AgentChunk, c) for c in agent_chunks_raw]

    # --------------------------------------------------------------
    # Step 7: Token budget enforcement
    # --------------------------------------------------------------
    context_parts: List[str] = []
    token_count = 0

    for c in agent_chunks:
        tokens = len(str(c["text"]).split())
        if token_count + tokens > max_total_tokens:
            break
        context_parts.append(str(c["text"]))
        token_count += tokens

    context_str = "\n\n".join(context_parts)
    logger.info("Final context tokens ~%d", token_count)

    # --------------------------------------------------------------
    # Step 8: Call LLM
    # --------------------------------------------------------------
    llm_payload = {"context": context_str, "query": query}
    params: Dict[str, str] = {}
    if provider:
        params["provider"] = provider
    if model:
        params["model"] = model

    llm_url = f"{settings.LLM_SERVICE_URL}/generate"

    async with httpx.AsyncClient( timeout=120) as client:
        try:
            resp = await client.post(llm_url, json=llm_payload, params=params)
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    sources = [c["document_id"] for c in agent_chunks]

    return RAGResult(
        answer=result.get("response", ""),
        sources=sources,
    )
