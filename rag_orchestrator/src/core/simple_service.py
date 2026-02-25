# rag_orchestrator/src/core/simple_service.py
"""
Simple (graph-unaware) RAG pipeline.
For regular documents: PDFs, text files, etc.
No graph traversal, no repo_id required.
"""
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


class SimpleRAGResult(BaseModel):
    answer: str
    sources: List[str]


async def run_simple_rag(
    query: str,
    top_k: int = 20,
    max_chunks_per_doc: int = 5,
    max_total_tokens: int = 2048,
    provider: str | None = None,
    model: str | None = None,
    chunk_filter_fn: Optional[Callable[[RetrievedChunk], bool]] = None,
) -> SimpleRAGResult:

    settings = get_settings()

    # Step 1: Embed query
    embedder = get_embedder(
        provider=settings.EMBEDDING_PROVIDER,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_model=settings.OLLAMA_EMBED_MODEL,
        ollama_batch_size=settings.OLLAMA_BATCH_SIZE,
    )
    query_embedding = embed_query(query, embedder)

    # Step 2: Vector search - no metadata filter, searches all docs
    search_url = f"{settings.VECTOR_STORE_URL}/v1/vectors/search"
    payload = {"query_vector": query_embedding, "k": top_k,
                "metadata_filter": {"source_type": {"ne": "code"}}}

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(search_url, json=payload)
            resp.raise_for_status()
            raw_results = resp.json().get("results", [])
        except Exception as e:
            logger.error("Vector search failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    # Step 3: Build chunks
    seed_document_ids: List[str] = []
    seen: set = set()
    retrieved_chunks_by_document: Dict[str, List[RetrievedChunk]] = {}

    for r in raw_results:
        doc_id = r.get("document_id") or r.get("metadata", {}).get("document_id")
        if not doc_id:
            continue
        if doc_id not in seen:
            seen.add(doc_id)
            seed_document_ids.append(doc_id)
        chunk = RetrievedChunk(
            document_id=doc_id,
            chunk_id=r["chunk_id"],
            text=r["text"],
            score=r.get("score"),
            metadata=r.get("metadata", {}),
        )
        retrieved_chunks_by_document.setdefault(doc_id, []).append(chunk)

    logger.info("Simple RAG: %d seed documents", len(seed_document_ids))

    # Step 4: RetrievalPlan + execute
    plan = RetrievalPlan(
        seed_document_ids=set(seed_document_ids),
        expanded_document_ids=set(),
        expansion_metadata={},
    )
    retrieved_context = execute_retrieval_plan(
        plan=plan,
        retrieved_chunks_by_document=retrieved_chunks_by_document,
        debug=True,
    )

    # Step 5: Prepare chunks
    agent_chunks_raw = prepare_chunks_for_agent(
        retrieved_context,
        document_order=seed_document_ids,
        max_chunks_per_doc=max_chunks_per_doc,
        max_total_chunks=9999,
        filter_chunk=chunk_filter_fn,
        debug=True,
    )
    agent_chunks = [cast(Dict[str, Any], c) for c in agent_chunks_raw]

    # Step 6: Token budget
    context_parts: List[str] = []
    token_count = 0
    for c in agent_chunks:
        tokens = len(str(c["text"]).split())
        if token_count + tokens > max_total_tokens:
            break
        context_parts.append(str(c["text"]))
        token_count += tokens
    context_str = "\n\n".join(context_parts)

    # Step 7: LLM call
    llm_payload = {"context": context_str, "query": query}
    params: Dict[str, str] = {}
    if provider:
        params["provider"] = provider
    if model:
        params["model"] = model

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(
                f"{settings.LLM_SERVICE_URL}/generate",
                json=llm_payload,
                params=params
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    return SimpleRAGResult(
        answer=result.get("response", ""),
        sources=[c["document_id"] for c in agent_chunks],
    )