"""REST API routes for job submission and status tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from vecinita_scraper.app import scrape_jobs_queue
from vecinita_scraper.core.db import PostgresDB
from vecinita_scraper.core.errors import DatabaseError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import (
    ChunkingConfig,
    CrawlConfig,
    JobStatus,
    JobStatusResponse,
    ScrapeJobQueueData,
    ScrapeJobRequest,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = get_logger(__name__)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new scraping job",
    description="Enqueues a URL for scraping and begins the job processing pipeline.",
)
async def submit_job(request: ScrapeJobRequest) -> dict[str, Any]:
    """
    Submit a new scraping job.

    The job will be enqueued for:
    1. Web crawling (Crawl4AI)
    2. Document processing (Docling)
    3. Semantic chunking
    4. Embedding generation
    5. Final storage

    Args:
        request: ScrapeJobRequest with URL, configs, and user_id

    Returns:
        dict with job_id, status, and created_at

    Raises:
        HTTPException: For invalid input or database errors
    """
    try:
        db = PostgresDB()

        # Use provided configs or defaults
        crawl_config = request.crawl_config or CrawlConfig()
        chunking_config = request.chunking_config or ChunkingConfig()

        # Create job in database
        job_id = await db.create_scraping_job(
            url=str(request.url),
            user_id=request.user_id,
            crawl_config=crawl_config.model_dump(),
            chunking_config=chunking_config.model_dump(),
            metadata=request.metadata,
        )

        logger.info(
            "Job submitted",
            job_id=job_id,
            url=str(request.url),
            user_id=request.user_id,
        )

        # Enqueue for scraping
        scrape_payload = ScrapeJobQueueData(
            job_id=job_id,
            url=str(request.url),
            user_id=request.user_id,
            crawl_config=crawl_config,
        )

        await scrape_jobs_queue.put.aio(scrape_payload.model_dump())

        return {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "url": str(request.url),
        }

    except DatabaseError as e:
        logger.exception("Database error during job submission", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e
    except ValidationError as e:
        logger.warning("Validation error during job submission", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error during job submission", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Retrieve the current status and progress of a scraping job.",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a scraping job.

    Args:
        job_id: UUID of the scraping job

    Returns:
        JobStatusResponse with current status, progress, and metadata

    Raises:
        HTTPException: For invalid job_id or database errors
    """
    try:
        db = PostgresDB()

        # Get job from database
        job_data = await db.get_job_status(job_id)

        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Calculate progress based on status
        status_to_progress = {
            JobStatus.PENDING: 5,
            JobStatus.VALIDATING: 10,
            JobStatus.CRAWLING: 20,
            JobStatus.EXTRACTING: 35,
            JobStatus.PROCESSING: 50,
            JobStatus.CHUNKING: 65,
            JobStatus.EMBEDDING: 80,
            JobStatus.STORING: 95,
            JobStatus.COMPLETED: 100,
            JobStatus.FAILED: 0,
            JobStatus.CANCELLED: 0,
        }

        current_status = JobStatus(job_data.get("status", JobStatus.PENDING))
        progress_pct = status_to_progress.get(current_status, 0)

        return JobStatusResponse(
            job_id=job_id,
            status=current_status,
            progress_pct=progress_pct,
            current_step=current_status.value,
            error_message=job_data.get("error_message"),
            updated_at=_coerce_datetime(job_data.get("updated_at")),
            created_at=_coerce_datetime(job_data.get("created_at")),
            crawl_url_count=job_data.get("crawl_url_count", 0),
            chunk_count=job_data.get("chunk_count", 0),
            embedding_count=job_data.get("embedding_count", 0),
        )

    except HTTPException:
        raise
    except DatabaseError as e:
        logger.exception("Database error retrieving job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving job status",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error retrieving job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "",
    response_model=dict[str, Any],
    summary="List jobs",
    description="List recent scraping jobs (limited to last 50).",
)
async def list_jobs(user_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """
    List recent scraping jobs.

    Args:
        user_id: Filter by user_id (optional)
        limit: Maximum number of jobs to return (1-100, default 50)

    Returns:
        dict with list of jobs and total count

    Raises:
        HTTPException: For invalid parameters or database errors
    """
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit must be between 1 and 100",
        )

    try:
        db = PostgresDB()
        result = await db.list_jobs(user_id=user_id, limit=limit)
        return {
            "user_id": user_id,
            "limit": limit,
            "jobs": result["jobs"],
            "total": result["total"],
        }

    except DatabaseError as e:
        logger.exception("Database error listing jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error listing jobs",
        ) from e
    except Exception as e:
        logger.exception("Error listing jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing jobs",
        ) from e


@router.post(
    "/{job_id}/cancel",
    response_model=dict[str, Any],
    summary="Cancel a job",
    description="Cancel a scraping job if it hasn't completed.",
)
async def cancel_job(job_id: str) -> dict[str, Any]:
    """
    Cancel a scraping job.

    Can only cancel jobs that haven't reached COMPLETED, FAILED, or CANCELLED status.

    Args:
        job_id: UUID of the scraping job

    Returns:
        dict with job_id, previous_status, and new_status

    Raises:
        HTTPException: For invalid job_id, database errors, or if job can't be cancelled
    """
    try:
        db = PostgresDB()

        # Get current job status
        job_data = await db.get_job_status(job_id)

        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        current_status = JobStatus(job_data.get("status", JobStatus.PENDING))

        # Check if job can be cancelled
        non_cancellable_statuses = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
        if current_status in non_cancellable_statuses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot cancel job with status {current_status.value}",
            )

        # Update status to CANCELLED
        await db.update_job_status(job_id, JobStatus.CANCELLED.value)

        logger.info("Job cancelled", job_id=job_id, previous_status=current_status.value)

        return {
            "job_id": job_id,
            "previous_status": current_status.value,
            "new_status": JobStatus.CANCELLED.value,
        }

    except HTTPException:
        raise
    except DatabaseError as e:
        logger.exception("Database error cancelling job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error cancelling job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
