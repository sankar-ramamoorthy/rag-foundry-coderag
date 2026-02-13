from fastapi import APIRouter

from src.api.v1.ingest import router as ingest_router
from src.api.v1.summary import router as ingest_summary

router = APIRouter(prefix="/v1")

router.include_router(ingest_router)
router.include_router(ingest_summary)
