import logging
import document_service.buckets as s3
import document_service.tables as db

from contextlib import asynccontextmanager

logger = logging.getLogger("uvicorn.access")


__DOCUMENTS = "nmp-autoavanza-documents"


@asynccontextmanager
async def lifespan(app):
    logger.info("Provisioning bucket and table....")
    s3.create_bucket(__DOCUMENTS)
    db.create_table(__DOCUMENTS)
    yield
    logger.info("Server shutting down!")
