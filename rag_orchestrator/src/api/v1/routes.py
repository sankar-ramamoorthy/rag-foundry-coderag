# api.py

import logging

from src.api.v1.models import RAGQuery, RAGResponse, SearchQuery
from src.core.service import run_rag#, search_documents
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# /search endpoint to get vector search results without invoking the LLM
#@router.post("/search")
#async def search_endpoint(query: SearchQuery):
#    logger.debug(f"Received search query: {query}")
#
#    try:
#        # Get search results from the service layer
#        results = await search_documents(query.question, query.top_k)
#        return {"results": results}

#    except Exception as e:
#        logger.error(f"Error occurred while searching: {e}")
#        raise HTTPException(
#            status_code=500, detail="An error occurred during the search."
#        )


# /rag endpoint to run the full RAG (retrieval-augmented generation) process
@router.post("/rag", response_model=RAGResponse)
async def rag_endpoint(rag_query: RAGQuery):
    logger.debug(f"Received RAG query: {rag_query}")

    try:
        # Call the service layer to perform the full RAG process
        #result = await run_rag(
        #    rag_query.query, rag_query.top_k, rag_query.provider, rag_query.model
        #)
        result = await run_rag(
        query=rag_query.query,
        top_k=rag_query.top_k,
        provider=rag_query.provider,
        model=rag_query.model
        )
        return result

    except Exception as e:
        logger.error(f"Error occurred during the RAG process: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the RAG request.",
        )
