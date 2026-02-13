from typing import List, Optional

from pydantic import BaseModel


# Model to handle the search query and its parameters
class SearchQuery(BaseModel):
    question: str
    top_k: int = 5  # Default to top 5 search results


# Model for the RAG (retrieval-augmented generation) query input
class RAGQuery(BaseModel):
    query: str
    top_k: int = 5
    provider: Optional[str] = None  # Optional: If specified, will be passed to the LLM
    model: Optional[str] = None  # Optional: If specified, will be passed to the LLM


# Model for the response from the RAG process
class RAGResponse(BaseModel):
    answer: str
    sources: List[str]  # List of sources from which the answer was generated
