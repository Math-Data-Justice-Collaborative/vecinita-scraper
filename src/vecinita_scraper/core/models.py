"""Pydantic data models for API and queue communication."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class JobStatus(StrEnum):
    """Job status progression throughout the pipeline."""

    PENDING = "pending"
    VALIDATING = "validating"
    CRAWLING = "crawling"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlConfig(BaseModel):
    """Tuning knobs for the Crawl4AI crawl stage."""

    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum link depth to follow from the seed URL.",
        examples=[3],
    )
    timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Per-page navigation timeout in seconds.",
        examples=[60],
    )
    headless: bool = Field(default=True, description="Run the browser headless.", examples=[True])
    wait_for_content: bool = Field(
        default=True,
        description="Wait for dynamic content before extraction.",
        examples=[True],
    )
    include_links: bool = Field(
        default=True,
        description="Whether discovered links are enqueued for deeper crawling.",
        examples=[True],
    )
    include_images: bool = Field(
        default=False,
        description="Whether to download image assets (higher bandwidth).",
        examples=[False],
    )


class ChunkingConfig(BaseModel):
    """Semantic chunking parameters applied after Docling extraction."""

    min_size_tokens: int = Field(
        default=256,
        ge=100,
        description="Soft minimum chunk size in tokenizer tokens.",
        examples=[256],
    )
    max_size_tokens: int = Field(
        default=1024,
        ge=200,
        description="Hard maximum chunk size in tokenizer tokens.",
        examples=[1024],
    )
    overlap_ratio: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="Fraction of overlap between adjacent chunks.",
        examples=[0.2],
    )
    split_by_sentence: bool = Field(
        default=True,
        description="Prefer sentence boundaries when splitting.",
        examples=[True],
    )


class ScrapeJobRequest(BaseModel):
    """Request to submit a new scraping job."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://example.org/community-resources",
                    "user_id": "operator-42",
                    "crawl_config": {"max_depth": 2, "timeout_seconds": 90},
                    "chunking_config": {"min_size_tokens": 300, "max_size_tokens": 900},
                    "metadata": {"source": "schemathesis-example"},
                }
            ]
        }
    )

    url: HttpUrl = Field(..., description="HTTP or HTTPS seed URL for the crawl pipeline.")
    user_id: str = Field(
        ...,
        min_length=1,
        description="Opaque operator or tenant id used for auditing and filtering.",
        examples=["operator-42"],
    )
    crawl_config: CrawlConfig | None = Field(
        default=None,
        description="Optional crawl overrides (defaults are sensible for most sites).",
    )
    chunking_config: ChunkingConfig | None = Field(
        default=None,
        description="Optional chunking overrides for downstream embedding.",
    )
    llm_extraction_prompt: str | None = Field(
        default=None,
        description="Optional prompt guiding LLM-assisted extraction.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary JSON metadata stored with the job.",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate URL is HTTP/HTTPS."""
        if v.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        return v


class CrawledURLData(BaseModel):
    """Data about a crawled URL."""

    job_id: str
    url: str
    raw_content: str
    content_hash: str
    status: str  # "success", "failed", "timeout", etc.
    error_message: str | None = None
    crawled_at: datetime


class ExtractedContentData(BaseModel):
    """Raw extracted content before processing."""

    crawled_url_id: str
    content_type: str  # "markdown", "html", "pdf", etc.
    raw_content: str
    processing_status: str  # "pending", "processing", "completed", "failed"


class ProcessedDocumentData(BaseModel):
    """Document after processing with Docling."""

    extracted_content_id: str
    markdown_content: str
    tables_json: str | None = None
    metadata_json: str | None = None


class ChunkData(BaseModel):
    """Semantic chunk of processed content."""

    processed_doc_id: str
    chunk_text: str
    position: int
    token_count: int
    semantic_boundary: bool


class EmbeddingData(BaseModel):
    """Embedding vector with metadata."""

    chunk_id: str
    embedding_vector: list[float]
    model_name: str
    dimensions: int


class JobStatusResponse(BaseModel):
    """Current status of a scraping job."""

    job_id: str
    status: JobStatus
    progress_pct: int = Field(ge=0, le=100)
    current_step: str
    error_message: str | None = None
    updated_at: datetime
    created_at: datetime
    crawl_url_count: int = 0
    chunk_count: int = 0
    embedding_count: int = 0


class ChunkWithEmbedding(BaseModel):
    """Chunk with its embedding for search."""

    chunk_id: str
    text: str
    embedding: list[float]
    position: int
    url: str
    metadata: dict[str, Any] = {}


class EmbeddingModelConfig(BaseModel):
    """Configuration of the embedding model from API."""

    model_name: str
    dimensions: int
    max_tokens: int
    batch_size: int = 100


# Queue and internal messaging models


class ScrapeJobQueueData(BaseModel):
    """Data sent to scrape-jobs queue."""

    job_id: str
    url: str
    user_id: str
    crawl_config: CrawlConfig
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessJobQueueData(BaseModel):
    """Data sent to process-jobs queue."""

    job_id: str
    crawled_url_id: str
    extracted_content_id: str
    raw_content: str
    content_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChunkJobQueueData(BaseModel):
    """Data sent to chunk-jobs queue."""

    job_id: str
    processed_doc_id: str
    markdown_content: str
    chunking_config: ChunkingConfig | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmbedJobQueueData(BaseModel):
    """Data sent to embed-jobs queue."""

    job_id: str
    chunk_ids: list[str]
    chunk_texts: list[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StoreJobQueueData(BaseModel):
    """Data sent to store-jobs queue."""

    job_id: str
    embedding_ids: list[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
