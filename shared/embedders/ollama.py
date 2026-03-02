# src/ingestion_service/core/embedders/ollama.py
import requests
import logging
from typing import List
from shared.embedders.base import BaseEmbedder
from shared.chunks import Chunk

logging.basicConfig(level=logging.DEBUG)

# mxbai-embed-large context window is 512 tokens.
# We truncate conservatively at 400 words (words ≈ tokens for English/code).
# This prevents "input length exceeds context length" errors on large chunks.
MAX_EMBEDDING_WORDS = 400


def _truncate(text: str, max_words: int = MAX_EMBEDDING_WORDS) -> str:
    """Truncate text to max_words words to stay within embedding model context."""
    words = text.split()
    if len(words) <= max_words:
        return text
    truncated = " ".join(words[:max_words])
    logging.debug(
        "OllamaEmbedder: truncated chunk from %d words to %d words",
        len(words), max_words,
    )
    return truncated


class OllamaEmbedder(BaseEmbedder):
    name = "ollama"

    def __init__(self, base_url: str, model: str, batch_size: int = 50, dimension: int = 1024):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = batch_size
        self.dimension = dimension  # driven by VECTOR_DIMENSION in each service's config
        logging.debug("OllamaEmbedder base_url=%s model=%s dimension=%d", 
                      self.base_url, self.model, self.dimension)

    def embed(self, chunks: List[Chunk]) -> List[List[float]]:
        logging.debug(
            "OllamaEmbedder received %d items, types: %s",
            len(chunks),
            [type(c).__name__ for c in chunks[:3]],
        )
        # Truncate each chunk to stay within mxbai-embed-large context window
        texts = [_truncate(chunk.content) for chunk in chunks]

        try:
            payload = {"model": self.model, "input": texts}
            logging.debug("OllamaEmbedder starting embedding")
            response = requests.post(f"{self.base_url}/api/embed", json=payload)
            logging.debug("OllamaEmbedder finished embedding")
            logging.debug("OllamaEmbedder response: %s", response)

            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama embedding failed "
                    f"(status={response.status_code}): {response.text}"
                )

            result = response.json()
            logging.debug("OllamaEmbedder response.json: %s", result)
            return (
                result.get("embeddings", [result["embeddings"]])
                if isinstance(texts, list)
                else [result["embeddings"]]
            )
        except Exception as e:
            raise RuntimeError(f"Ollama embedder error: {e}") from e