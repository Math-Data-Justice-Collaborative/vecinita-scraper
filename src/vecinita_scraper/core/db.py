"""Database utilities for Supabase integration."""

from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from vecinita_scraper.core.config import get_config
from vecinita_scraper.core.errors import DatabaseError
from vecinita_scraper.core.logger import get_logger

logger = get_logger(__name__)


class SupabaseDB:
    """Supabase database client wrapper."""

    def __init__(self, client: Any | None = None) -> None:
        """Initialize Supabase client."""
        if client:
            self.client = client
        else:
            try:
                from supabase import create_client
            except ImportError as exc:
                raise DatabaseError(
                    "supabase is not installed. Install project dependencies"
                    " before using the database client."
                ) from exc
            config = get_config()
            api_key = config.supabase.service_key or config.supabase.anon_key
            self.client = create_client(
                config.supabase.project_url,
                api_key,
            )

    async def create_scraping_job(
        self,
        url: str,
        user_id: str,
        crawl_config: dict[str, Any],
        chunking_config: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new scraping job and return job_id."""
        job_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        try:
            self.client.table("scraping_jobs").insert(
                {
                    "id": job_id,
                    "url": url,
                    "user_id": user_id,
                    "status": "pending",
                    "crawl_config": crawl_config,
                    "chunking_config": chunking_config,
                    "metadata": metadata or {},
                    "created_at": now,
                    "updated_at": now,
                }
            ).execute()

            logger.info("Created scraping job", job_id=job_id, user_id=user_id, url=url)
            return job_id
        except Exception as e:
            raise DatabaseError(f"Failed to create scraping job: {str(e)}") from e

    async def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get the status of a scraping job."""
        try:
            result = (
                self.client.table("scraping_jobs").select("*").eq("id", job_id).single().execute()
            )
            return cast(dict[str, Any], result.data)
        except Exception as e:
            raise DatabaseError(f"Failed to get job status: {str(e)}") from e

    async def update_job_status(
        self, job_id: str, status: str, error_message: str | None = None
    ) -> None:
        """Update job status."""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if error_message:
            update_data["error_message"] = error_message

        try:
            self.client.table("scraping_jobs").update(update_data).eq("id", job_id).execute()
            logger.info("Updated job status", job_id=job_id, status=status)
        except Exception as e:
            raise DatabaseError(f"Failed to update job status: {str(e)}") from e

    async def store_crawled_url(
        self,
        job_id: str,
        url: str,
        raw_content: str,
        content_hash: str,
        status: str = "success",
        error_message: str | None = None,
    ) -> str:
        """Store crawled URL data and return crawled_url_id."""
        crawled_url_id = str(uuid4())

        try:
            self.client.table("crawled_urls").insert(
                {
                    "id": crawled_url_id,
                    "job_id": job_id,
                    "url": url,
                    "raw_content_hash": content_hash,
                    "status": status,
                    "error_message": error_message,
                    "crawled_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            logger.info("Stored crawled URL", job_id=job_id, url=url)
            return crawled_url_id
        except Exception as e:
            raise DatabaseError(f"Failed to store crawled URL: {str(e)}") from e

    async def store_extracted_content(
        self,
        crawled_url_id: str,
        content_type: str,
        raw_content: str,
    ) -> str:
        """Store extracted content and return extracted_content_id."""
        extracted_content_id = str(uuid4())

        try:
            self.client.table("extracted_content").insert(
                {
                    "id": extracted_content_id,
                    "crawled_url_id": crawled_url_id,
                    "content_type": content_type,
                    "raw_content": raw_content,
                    "processing_status": "pending",
                }
            ).execute()

            logger.info("Stored extracted content", extracted_content_id=extracted_content_id)
            return extracted_content_id
        except Exception as e:
            raise DatabaseError(f"Failed to store extracted content: {str(e)}") from e

    async def store_processed_document(
        self,
        extracted_content_id: str,
        markdown_content: str,
        tables_json: str | None = None,
        metadata_json: str | None = None,
    ) -> str:
        """Store processed document and return processed_doc_id."""
        processed_doc_id = str(uuid4())

        try:
            self.client.table("processed_documents").insert(
                {
                    "id": processed_doc_id,
                    "extracted_content_id": extracted_content_id,
                    "markdown_content": markdown_content,
                    "tables_json": tables_json,
                    "metadata_json": metadata_json,
                }
            ).execute()

            logger.info("Stored processed document", processed_doc_id=processed_doc_id)
            return processed_doc_id
        except Exception as e:
            raise DatabaseError(f"Failed to store processed document: {str(e)}") from e

    async def store_chunks(self, processed_doc_id: str, chunks: list[dict[str, Any]]) -> list[str]:
        """Store chunks and return list of chunk_ids."""
        chunk_ids = []

        try:
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid4())
                self.client.table("chunks").insert(
                    {
                        "id": chunk_id,
                        "processed_doc_id": processed_doc_id,
                        "chunk_text": chunk["text"],
                        "position": i,
                        "token_count": chunk.get("token_count", 0),
                        "semantic_boundary": chunk.get("semantic_boundary", False),
                    }
                ).execute()
                chunk_ids.append(chunk_id)

            logger.info("Stored chunks", processed_doc_id=processed_doc_id, count=len(chunk_ids))
            return chunk_ids
        except Exception as e:
            raise DatabaseError(f"Failed to store chunks: {str(e)}") from e

    async def store_embeddings(self, job_id: str, chunk_embeddings: list[dict[str, Any]]) -> None:
        """Store embeddings."""
        try:
            for embedding_data in chunk_embeddings:
                self.client.table("embeddings").insert(
                    {
                        "id": str(uuid4()),
                        "job_id": job_id,
                        "chunk_id": embedding_data["chunk_id"],
                        "embedding_vector": embedding_data["embedding"],
                        "model_name": embedding_data.get("model_name", "BAAI/bge-small-en-v1.5"),
                        "dimensions": embedding_data.get("dimensions", 384),
                        "created_at": datetime.utcnow().isoformat(),
                    }
                ).execute()

            logger.info("Stored embeddings", job_id=job_id, count=len(chunk_embeddings))
        except Exception as e:
            raise DatabaseError(f"Failed to store embeddings: {str(e)}") from e

    async def get_job_chunks_with_embeddings(
        self, job_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get chunks with embeddings for a job."""
        try:
            result = (
                self.client.from_("embeddings")
                .select("chunks(*), embeddings(*)")
                .eq("job_id", job_id)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            raise DatabaseError(f"Failed to get chunks with embeddings: {str(e)}") from e


_db_instance: SupabaseDB | None = None


def get_db() -> SupabaseDB:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance


def set_db(db: SupabaseDB) -> None:
    """Set database instance (for testing)."""
    global _db_instance
    _db_instance = db
