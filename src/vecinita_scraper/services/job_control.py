"""Scrape job control plane: Postgres + Modal queue (used by REST and Modal RPC)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ValidationError

from vecinita_scraper.core.db import PostgresDB
from vecinita_scraper.core.errors import DatabaseError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import (
    ChunkingConfig,
    CrawlConfig,
    JobStatus,
    JobStatusResponse,
    ScrapeJobCancelResponse,
    ScrapeJobCreatedResponse,
    ScrapeJobListItem,
    ScrapeJobListQueryParams,
    ScrapeJobListResponse,
    ScrapeJobQueueData,
    ScrapeJobRequest,
)

logger = get_logger(__name__)


class JobNotFoundError(Exception):
    """Raised when a job_id does not exist in the database."""


class JobConflictError(Exception):
    """Raised when an operation conflicts with the current job state (e.g. cancel completed job)."""


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()


_STATUS_TO_PROGRESS: dict[JobStatus, int] = {
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


_NON_CANCELLABLE: frozenset[JobStatus] = frozenset(
    {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
)


async def submit_scrape_job(
    request: ScrapeJobRequest,
    *,
    jobs_queue: Any,
) -> ScrapeJobCreatedResponse:
    """Create DB row and enqueue scrape work."""
    db = PostgresDB()
    crawl_config = request.crawl_config or CrawlConfig()
    chunking_config = request.chunking_config or ChunkingConfig()

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

    scrape_payload = ScrapeJobQueueData(
        job_id=job_id,
        url=str(request.url),
        user_id=request.user_id,
        crawl_config=crawl_config,
    )
    await jobs_queue.put.aio(scrape_payload.model_dump())

    return ScrapeJobCreatedResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=datetime.utcnow().isoformat(),
        url=str(request.url),
    )


async def get_scrape_job_status(job_id: str) -> JobStatusResponse:
    """Return job status or raise JobNotFoundError."""
    db = PostgresDB()
    job_data = await db.get_job_status(job_id)
    if not job_data:
        raise JobNotFoundError(job_id)

    current_status = JobStatus(job_data.get("status", JobStatus.PENDING))
    progress_pct = _STATUS_TO_PROGRESS.get(current_status, 0)

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


async def list_scrape_jobs(params: ScrapeJobListQueryParams) -> ScrapeJobListResponse:
    """List recent jobs from Postgres."""
    db = PostgresDB()
    result = await db.list_jobs(user_id=params.user_id, limit=params.limit)
    jobs = [ScrapeJobListItem.model_validate(row) for row in result["jobs"]]
    return ScrapeJobListResponse(
        user_id=params.user_id,
        limit=params.limit,
        jobs=jobs,
        total=result["total"],
    )


async def cancel_scrape_job(job_id: str) -> ScrapeJobCancelResponse:
    """Cancel a job or raise JobNotFoundError / JobConflictError."""
    db = PostgresDB()
    job_data = await db.get_job_status(job_id)
    if not job_data:
        raise JobNotFoundError(job_id)

    current_status = JobStatus(job_data.get("status", JobStatus.PENDING))
    if current_status in _NON_CANCELLABLE:
        raise JobConflictError(f"Cannot cancel job with status {current_status.value}")

    await db.update_job_status(job_id, JobStatus.CANCELLED.value)
    logger.info("Job cancelled", job_id=job_id, previous_status=current_status.value)

    return ScrapeJobCancelResponse(
        job_id=job_id,
        previous_status=current_status.value,
        new_status=JobStatus.CANCELLED.value,
    )


# --- Modal RPC helpers (plain dict in/out for ``modal.Function`` callers) ---


def _rpc_ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _rpc_err(*, code: str, detail: str, http_status: int) -> dict[str, Any]:
    return {"ok": False, "code": code, "detail": detail, "http_status": http_status}


def modal_job_submit(payload: dict[str, Any], *, jobs_queue: Any) -> dict[str, Any]:
    """Sync entry for Modal: validate payload, run async submit, return envelope."""
    import asyncio

    try:
        request = ScrapeJobRequest.model_validate(payload)
    except ValidationError as exc:
        return _rpc_err(code="validation_error", detail=str(exc), http_status=422)

    async def _run() -> ScrapeJobCreatedResponse:
        return await submit_scrape_job(request, jobs_queue=jobs_queue)

    try:
        out = asyncio.run(_run())
        return _rpc_ok(out.model_dump(mode="json"))
    except DatabaseError as exc:
        logger.exception("Database error during job submission", error=str(exc))
        return _rpc_err(code="database_error", detail=str(exc), http_status=500)
    except Exception as exc:
        logger.exception("Unexpected error during job submission", error=str(exc))
        return _rpc_err(code="internal_error", detail=str(exc), http_status=500)


def modal_job_get(job_id: str) -> dict[str, Any]:
    import asyncio

    async def _run() -> JobStatusResponse:
        return await get_scrape_job_status(job_id)

    try:
        out = asyncio.run(_run())
        return _rpc_ok(out.model_dump(mode="json"))
    except JobNotFoundError:
        return _rpc_err(code="not_found", detail=f"Job {job_id} not found", http_status=404)
    except DatabaseError as exc:
        logger.exception("Database error retrieving job status", job_id=job_id, error=str(exc))
        return _rpc_err(code="database_error", detail=str(exc), http_status=500)
    except Exception as exc:
        logger.exception("Unexpected error retrieving job status", job_id=job_id, error=str(exc))
        return _rpc_err(code="internal_error", detail=str(exc), http_status=500)


def modal_job_list(user_id: str | None, limit: int) -> dict[str, Any]:
    import asyncio

    params = ScrapeJobListQueryParams(user_id=user_id, limit=limit)

    async def _run() -> ScrapeJobListResponse:
        return await list_scrape_jobs(params)

    try:
        out = asyncio.run(_run())
        return _rpc_ok(out.model_dump(mode="json"))
    except DatabaseError as exc:
        logger.exception("Database error listing jobs", error=str(exc))
        return _rpc_err(code="database_error", detail=str(exc), http_status=500)
    except Exception as exc:
        logger.exception("Error listing jobs", error=str(exc))
        return _rpc_err(code="internal_error", detail=str(exc), http_status=500)


def modal_job_cancel(job_id: str) -> dict[str, Any]:
    import asyncio

    async def _run() -> ScrapeJobCancelResponse:
        return await cancel_scrape_job(job_id)

    try:
        out = asyncio.run(_run())
        return _rpc_ok(out.model_dump(mode="json"))
    except JobNotFoundError:
        return _rpc_err(code="not_found", detail=f"Job {job_id} not found", http_status=404)
    except JobConflictError as exc:
        return _rpc_err(code="conflict", detail=str(exc), http_status=409)
    except DatabaseError as exc:
        logger.exception("Database error cancelling job", job_id=job_id, error=str(exc))
        return _rpc_err(code="database_error", detail=str(exc), http_status=500)
    except Exception as exc:
        logger.exception("Unexpected error cancelling job", job_id=job_id, error=str(exc))
        return _rpc_err(code="internal_error", detail=str(exc), http_status=500)
