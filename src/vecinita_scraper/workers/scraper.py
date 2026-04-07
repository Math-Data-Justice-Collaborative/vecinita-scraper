"""Modal worker for site crawling with Crawl4AI."""

from __future__ import annotations

from typing import Any

from vecinita_scraper.app import APP_SECRETS, app, process_jobs_queue, scrape_jobs_queue
from vecinita_scraper.core.db import PostgresDB, get_db
from vecinita_scraper.core.errors import CrawlingError, ValidationError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import JobStatus, ProcessJobQueueData, ScrapeJobQueueData
from vecinita_scraper.crawlers.crawl4ai_adapter import Crawl4AIAdapter

logger = get_logger(__name__)


async def run_scrape_job(
    job_data: ScrapeJobQueueData,
    db: PostgresDB | None = None,
    process_queue: Any | None = None,
) -> dict[str, Any]:
    """Execute a scrape job and enqueue extracted content for processing."""
    database = db or get_db()
    queue = process_queue or process_jobs_queue

    if not job_data.url:
        raise ValidationError("Scrape job is missing a URL")

    await database.update_job_status(job_data.job_id, JobStatus.VALIDATING.value)
    await database.update_job_status(job_data.job_id, JobStatus.CRAWLING.value)

    adapter = Crawl4AIAdapter(job_data.crawl_config)
    pages = await adapter.crawl_site(job_data.url)

    if not pages:
        raise CrawlingError(f"No pages were crawled for {job_data.url}")

    await database.update_job_status(job_data.job_id, JobStatus.EXTRACTING.value)

    processed_count = 0
    failed_count = 0

    for page in pages:
        crawled_url_id = await database.store_crawled_url(
            job_id=job_data.job_id,
            url=page.url,
            raw_content=page.markdown or page.cleaned_html or page.html,
            content_hash=page.content_hash,
            status="success" if page.success else "failed",
            error_message=page.error_message,
        )

        if not page.success:
            failed_count += 1
            continue

        content_type = determine_content_type(page.url)
        raw_content = page.markdown or page.cleaned_html or page.html
        extracted_content_id = await database.store_extracted_content(
            crawled_url_id=crawled_url_id,
            content_type=content_type,
            raw_content=raw_content,
        )

        payload = ProcessJobQueueData(
            job_id=job_data.job_id,
            crawled_url_id=crawled_url_id,
            extracted_content_id=extracted_content_id,
            raw_content=raw_content,
            content_type=content_type,
        )
        await queue.put.aio(payload.model_dump(mode="json"))
        processed_count += 1

        logger.info(
            "Queued extracted page for processing",
            job_id=job_data.job_id,
            crawled_url_id=crawled_url_id,
            extracted_content_id=extracted_content_id,
            url=page.url,
        )

    if processed_count == 0:
        await database.update_job_status(
            job_data.job_id,
            JobStatus.FAILED.value,
            error_message="Crawling finished without any successful pages",
        )
        raise CrawlingError(f"Job {job_data.job_id} produced no successful pages")

    return {
        "job_id": job_data.job_id,
        "pages_crawled": len(pages),
        "pages_queued": processed_count,
        "pages_failed": failed_count,
        "next_status": JobStatus.PROCESSING.value,
    }


@app.function(timeout=900, retries=2, max_containers=10, secrets=APP_SECRETS)
async def scraper_worker(job_payload: dict[str, Any]) -> dict[str, Any]:
    """Modal entrypoint for processing a single scrape job."""
    job_data = ScrapeJobQueueData.model_validate(job_payload)

    try:
        result = await run_scrape_job(job_data)
    except Exception as exc:
        db = get_db()
        await db.update_job_status(job_data.job_id, JobStatus.FAILED.value, error_message=str(exc))
        logger.exception("Scrape job failed", job_id=job_data.job_id, url=job_data.url)
        raise

    db = get_db()
    await db.update_job_status(job_data.job_id, JobStatus.PROCESSING.value)
    logger.info("Scrape job completed", **result)
    return result


@app.function(timeout=120, max_containers=2, secrets=APP_SECRETS)
async def drain_scrape_queue(batch_size: int = 10) -> dict[str, int]:
    """Pull pending scrape jobs from the queue and fan them out to workers."""
    dispatched = 0

    for _ in range(batch_size):
        item = await scrape_jobs_queue.get.aio(block=False)
        if item is None:
            break
        await scraper_worker.spawn.aio(item)
        dispatched += 1

    logger.info("Dispatched scrape jobs from queue", dispatched=dispatched)
    return {"dispatched": dispatched}


def determine_content_type(url: str) -> str:
    """Best-effort content type inference from URL."""
    lowered = url.lower()
    if lowered.endswith(".pdf"):
        return "pdf"
    if lowered.endswith(".docx"):
        return "docx"
    if lowered.endswith(".html") or lowered.endswith(".htm"):
        return "html"
    return "markdown"
