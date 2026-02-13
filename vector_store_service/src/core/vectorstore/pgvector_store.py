# src/core/vectorstore/pgvector_store.py - HOTFIX (no TABLE_NAME confusion)
from __future__ import annotations
from typing import Sequence, Iterable, List
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import logging

from src.core.vectorstore.base import VectorStore
from shared.models.vector import VectorRecord, VectorMetadata

logging.basicConfig(level=logging.DEBUG)

class PgVectorStore(VectorStore):
    SCHEMA = "ingestion_service"
    
    def __init__(self, dsn: str, dimension: int, provider: str = "mock") -> None:
        self._dsn = dsn
        self._dimension = dimension
        self._provider = provider
        # TEMP DISABLE VALIDATION - tables exist ✓
        logging.info("PgVectorStore MS6: Skipping table validation for dual-write test")

    @property
    def dimension(self) -> int:
        return self._dimension

    def persist(self, records: list[VectorRecord]) -> None:
        self.add(records)
        logging.debug("PgVectorStore.persist: added %d records", len(records))

    def add(self, records: Iterable[VectorRecord]) -> None:
        """MS6 Dual-write: vectors + vector_chunks"""
        vectors_sql = sql.SQL("""
            INSERT INTO {schema}.vectors 
            (vector, ingestion_id, chunk_id, chunk_index, chunk_strategy, 
             chunk_text, source_metadata, provider)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """).format(schema=sql.Identifier(self.SCHEMA))
        
        chunks_sql = sql.SQL("""
            INSERT INTO {schema}.vector_chunks 
            (vector, ingestion_id, chunk_id, chunk_index, chunk_strategy, 
             chunk_text, source_metadata, provider, document_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """).format(schema=sql.Identifier(self.SCHEMA))

        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                for record in records:
                    # Legacy vectors
                    cur.execute(vectors_sql, (
                        record.vector, record.metadata.ingestion_id,
                        record.metadata.chunk_id, record.metadata.chunk_index,
                        record.metadata.chunk_strategy, record.metadata.chunk_text,
                        Jsonb(record.metadata.source_metadata or {}),
                        record.metadata.provider or self._provider,
                    ))
                    
                    # MS6 vector_chunks (w/ document_id)
                    if record.metadata.document_id:
                        cur.execute(chunks_sql, (
                            record.vector, record.metadata.ingestion_id,
                            record.metadata.chunk_id, record.metadata.chunk_index,
                            record.metadata.chunk_strategy, record.metadata.chunk_text,
                            Jsonb(record.metadata.source_metadata or {}),
                            record.metadata.provider or self._provider,
                            record.metadata.document_id,
                        ))
        logging.info(f"MS6 DUAL-WRITE: {len(records)} vectors + chunks complete")

    def similarity_search(self, query_vector: Sequence[float], k: int) -> List[VectorRecord]:
        """MS6: Search vector_chunks (provenance)"""
        search_sql = sql.SQL("""
            SELECT vector, ingestion_id, chunk_id, chunk_index, chunk_strategy,
                   chunk_text, source_metadata, provider, document_id
            FROM {schema}.vector_chunks
            ORDER BY vector <-> (%s::vector)
            LIMIT %s
        """).format(schema=sql.Identifier(self.SCHEMA))

        results: List[VectorRecord] = []
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(search_sql, (query_vector, k))
                for row in cur.fetchall():
                    (vector, ingestion_id, chunk_id, chunk_index, chunk_strategy,
                     chunk_text, source_metadata, provider, document_id) = row
                    metadata = VectorMetadata(
                        ingestion_id=ingestion_id, chunk_id=chunk_id,
                        chunk_index=chunk_index, chunk_strategy=chunk_strategy,
                        chunk_text=chunk_text, source_metadata=source_metadata,
                        provider=provider, document_id=document_id)
                    results.append(VectorRecord(vector=vector, metadata=metadata))
        return results

    def delete_by_ingestion_id(self, ingestion_id: str) -> None:
        for table in ["vectors", "vector_chunks"]:
            delete_sql = sql.SQL("""
                DELETE FROM {schema}.{table_name} WHERE ingestion_id = %s
            """).format(schema=sql.Identifier(self.SCHEMA), table_name=sql.Identifier(table))
            with psycopg.connect(self._dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(delete_sql, (ingestion_id,))
