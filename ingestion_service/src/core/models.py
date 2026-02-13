# ingestion_service/src/core/models.py (classic style - Pyright perfect)
import uuid
from sqlalchemy import Column, String, JSON, TIMESTAMP, MetaData  # ← Add MetaData here
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import text

metadata = MetaData(schema="ingestion_service")  # Now defined
Base = declarative_base(metadata=metadata)


class IngestionRequest(Base):
    __tablename__ = "ingestion_requests"
    __table_args__ = {"schema": "ingestion_service"}
    ingestion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String, nullable=False)
    ingestion_metadata = Column(JSON, nullable=True)
    status = Column(String, nullable=False, server_default=text("'pending'"))
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    started_at = Column(TIMESTAMP, nullable=True)
    finished_at = Column(TIMESTAMP, nullable=True)
