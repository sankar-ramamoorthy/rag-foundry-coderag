# ingestion_service/src/core/pipeline.py - MS6 COMPLETE (both run() + run_with_chunks)
from __future__ import annotations
from typing import Any, Optional
import logging
from uuid import uuid4, UUID


from shared.chunks import Chunk
from shared.chunkers.base import BaseChunker
from shared.chunkers.selector import ChunkerFactory
from src.core.database_session import get_sessionmaker
from src.core.crud.crud_document_node import create_document_node


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates the ingestion pipeline: validate → chunk → embed → persist.

    Two entry points:
    - run(): For text-based ingestion (extracts, chunks, embeds, persists)
    - run_with_chunks(): For pre-chunked content like PDFs (embeds, persists)
    """

    def __init__(
        self,
        *,
        validator,
        chunker: Optional[BaseChunker] = None,
        embedder,
        vector_store,
    ) -> None:
        self._validator = validator
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store

    def run(
        self,
        *,
        text: str,
        ingestion_id: str,
        source_type: str,
        provider: str,
    ) -> None:
        """
        Full pipeline: validate → chunk → embed → persist + DocumentNode (MS6).

        Use this for simple text ingestion (TXT files).
        """
        logger.debug("🔄 pipeline.py run() - TEXT PATH - Full MS6 pipeline: validate → chunk → DocumentNode → embed → persist")
        
        # MS6: Create DocumentNode FIRST (before any vectors)
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            document_id = uuid4()
            # 🔥 MS7 FIX: Use exact source format that summary.py expects
            source = f"file_document_{ingestion_id}"  # Full UUID to match summary.py
            title = f"{source_type}_document_{ingestion_id[:8]}"  # Keep title human-readable
            
            logger.debug(f"📝 MS6 run() Creating DocumentNode:")
            logger.debug(f"   ingestion_id: {ingestion_id}")
            logger.debug(f"   document_id: {document_id}")
            logger.debug(f"   title: '{title}'")
            logger.debug(f"   source: '{source}'")  # 🔥 MS7: This MUST match summary.py query
            
            create_document_node(
                session,
                document_id=document_id,
                title=title,
                summary="Document summary pending MS7",
                source=source,  # 🔥 MS7: Matches summary.py query
                ingestion_id=UUID(ingestion_id),
                doc_type=source_type,  # "file", "image", etc.
            )
            session.commit()  #  CRITICAL: Commit BEFORE vectors
            logger.debug(f"✅ MS6 run() DocumentNode COMMITTED {document_id} for {ingestion_id}")
            logger.debug(f"   → summary.py will look for source='{source}'")

        # Continue normal pipeline
        self._validate(text)
        chunks = self._chunk(
            text=text,
            source_type=source_type,
            provider=provider,
        )
        embeddings = self._embed(chunks)
        logger.debug(f"📦 MS6 run() Persisting {len(chunks)} chunks with document_id={document_id}")
        self._persist(chunks, embeddings, ingestion_id, str(document_id))

    def run_with_chunks(
        self,
        *,
        chunks: list[Chunk],
        ingestion_id: str,
    ) -> None:
        """
        Pipeline for pre-chunked content: DocumentNode → embed → persist (MS6).
        Use this for PDFs or other content where chunking happened upstream.
        """
        logger.debug(f"🔄 pipeline.py run_with_chunks() - PDF PATH - {len(chunks)} pre-chunked items")
        
        # MS6: Create DocumentNode FIRST
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            document_id = uuid4()
            # 🔥 MS7 FIX: Use exact source format that summary.py expects
            source = f"file_document_{ingestion_id}"  # Full UUID to match summary.py
            title = chunks[0].metadata.get("filename", "untitled") if chunks else "untitled"
            
            logger.debug(f"📝 MS6 run_with_chunks() Creating DocumentNode:")
            logger.debug(f"   ingestion_id: {ingestion_id}")
            logger.debug(f"   document_id: {document_id}")
            logger.debug(f"   title: '{title}'")
            logger.debug(f"   source: '{source}'")  # 🔥 MS7: This MUST match summary.py query
            
            create_document_node(
                session,
                document_id=document_id,
                title=title,
                summary="Document summary pending MS7",
                source=source,  # 🔥 MS7: Matches summary.py query
                ingestion_id=UUID(ingestion_id),
                doc_type="file",
            )
            session.commit()  # 🔥 CRITICAL: Commit BEFORE vectors
            logger.debug(f"✅ MS6 run_with_chunks() DocumentNode COMMITTED {document_id} for {ingestion_id}")
            logger.debug(f"   → summary.py will look for source='{source}'")

        # Continue pipeline
        embeddings = self._embed(chunks)
        logger.debug(f"📦 MS6 run_with_chunks() Persisting {len(chunks)} chunks with document_id={document_id}")
        self._persist(chunks, embeddings, ingestion_id, str(document_id))

    def _validate(self, text: str) -> None:
        """Validate input text (currently no-op)."""
        logger.debug("✅ pipeline.py _validate() - No-op validator passed")

    def _chunk(
        self,
        text: str,
        source_type: str,
        provider: str,
    ) -> list[Chunk]:
        """
        Chunk text using selected strategy.
        Adds provenance metadata to each chunk for provenance.
        """
        logger.debug(f"🔪 pipeline.py _chunk() text_len={len(text)} source_type={source_type}")
        
        if self._chunker is None:
            selected_chunker, chunker_params = ChunkerFactory.choose_strategy(text)
        else:
            selected_chunker = self._chunker
            chunker_params = {}

        chunks: list[Chunk] = selected_chunker.chunk(text, **chunker_params)
        chunk_strategy = getattr(selected_chunker, "chunk_strategy", "unknown")

        logger.debug(f"   → Selected chunker: {getattr(selected_chunker, 'name', selected_chunker.__class__.__name__)}")
        logger.debug(f"   → Strategy: {chunk_strategy}, Chunks produced: {len(chunks)}")

        # Add provenance metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata.update(
                {
                    "chunk_strategy": chunk_strategy,
                    "chunker_name": getattr(
                        selected_chunker,
                        "name",
                        selected_chunker.__class__.__name__,
                    ),
                    "chunker_params": dict(chunker_params),
                    "source_type": source_type,
                    "provider": provider,
                }
            )
            logger.debug(f"   → Chunk {i}: {len(chunk.content)} chars")

        return chunks

    def _embed(self, chunks: list[Chunk]) -> list[Any]:
        """
        Generate embeddings for chunks.
        Validates that embedding count matches chunk count.
        """
        logger.debug(f"🔗 pipeline.py _embed() {len(chunks)} chunks")
        embeddings = self._embedder.embed(chunks)

        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embedder mismatch: {len(chunks)} chunks, {len(embeddings)} embeddings"
            )

        logger.debug(f"✅ _embed() produced {len(embeddings)} embeddings ({len(embeddings[0])} dims each)")
        return embeddings

    def _persist(
        self,
        chunks: list[Chunk],
        embeddings: list[Any],
        ingestion_id: str,
        document_id: str,  # MS6-IS1: Link chunks to DocumentNode
    ) -> None:
        """
        Persist chunks and embeddings to vector store.
        """
        logger.debug(f"💾 pipeline.py _persist() {len(chunks)} chunks doc_id={document_id}")
        logger.debug(f"   → ingestion_id: {ingestion_id}")
        self._vector_store.persist(
            chunks=chunks,
            embeddings=embeddings,
            ingestion_id=ingestion_id,
            document_id=document_id,  # MS6-IS1: Pass to vector store
        )
        logger.debug(f"✅ _persist() COMPLETE for doc_id={document_id}")
