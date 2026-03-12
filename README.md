# vecinita-scraper

[![CI/CD - Deploy to Modal](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper/actions/workflows/ci-cd.yml)

Serverless web scraping pipeline on Modal with a FastAPI control plane, queue-driven workers, and Supabase-backed job state.

## Features

- Distributed queue-based worker pipeline (scrape -> process -> chunk -> embed -> store)
- FastAPI job API with validation via Pydantic models
- Modal deployment for workers and API app
- Supabase-backed job lifecycle tracking
- CI/CD deployment on push to `main`

## Quick Start

```bash
# Install
make dev-install

# Run test suite (non-live)
make test

# Local modal serve (API)
make serve

# Deploy both apps
modal auth login
make deploy
```

## System Architecture

```text
REST API (FastAPI)
  POST /jobs            -> enqueue scrape job
  GET  /jobs/{job_id}   -> read job status
  GET  /jobs            -> list jobs (placeholder response)
  POST /jobs/{job_id}/cancel -> cancel job

        |
        v
Supabase job records + Modal queues
  scrape-jobs -> process-jobs -> chunk-jobs -> embed-jobs -> store-jobs
```

## API Reference

Base path for job routes: `/jobs`

### Authentication

When proxy auth is enabled (`MODAL_PROXY_AUTH_ENABLED=true` and both secrets present), protected endpoints require:

- `x-modal-auth-key: <MODAL_AUTH_KEY>`
- `x-modal-auth-secret: <MODAL_AUTH_SECRET>`

Public (auth-exempt) endpoints:

- `GET /health`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`

### Data Models

#### `ScrapeJobRequest` (POST `/jobs` body)

| Field | Type | Required | Notes |
|---|---|---|---|
| `url` | string (http/https URL) | Yes | Must be a valid HTTP or HTTPS URL |
| `user_id` | string | Yes | Minimum length 1 |
| `crawl_config` | object (`CrawlConfig`) | No | Uses defaults when omitted |
| `chunking_config` | object (`ChunkingConfig`) | No | Uses defaults when omitted |
| `llm_extraction_prompt` | string | No | Optional custom extraction prompt |
| `metadata` | object | No | Arbitrary key/value metadata |

#### `CrawlConfig`

| Field | Type | Default | Constraints |
|---|---|---|---|
| `max_depth` | integer | `3` | `1 <= max_depth <= 10` |
| `timeout_seconds` | integer | `60` | `10 <= timeout_seconds <= 600` |
| `headless` | boolean | `true` | Browser mode |
| `wait_for_content` | boolean | `true` | Wait for dynamic page content |
| `include_links` | boolean | `true` | Include link extraction |
| `include_images` | boolean | `false` | Include image extraction |

#### `ChunkingConfig`

| Field | Type | Default | Constraints |
|---|---|---|---|
| `min_size_tokens` | integer | `256` | `min_size_tokens >= 100` |
| `max_size_tokens` | integer | `1024` | `max_size_tokens >= 200` |
| `overlap_ratio` | number | `0.2` | `0.0 <= overlap_ratio <= 0.5` |
| `split_by_sentence` | boolean | `true` | Sentence boundary splitting |

#### `JobStatus` enum

Pipeline progression:

`pending -> validating -> crawling -> extracting -> processing -> chunking -> embedding -> storing -> completed`

Terminal/error states:

`failed`, `cancelled`

#### Additional core models

| Model | Purpose |
|---|---|
| `CrawledURLData` | Captures crawled URL content and crawl status |
| `ExtractedContentData` | Stores raw extracted document content before processing |
| `ProcessedDocumentData` | Stores normalized markdown/doc output from processing |
| `ChunkData` | Represents semantic chunks with position and token counts |
| `EmbeddingData` | Represents embeddings for chunks with model metadata |
| `ChunkWithEmbedding` | Chunk payload plus embedding used for retrieval/search flows |
| `EmbeddingModelConfig` | Embedding model metadata (`dimensions`, `batch_size`, etc.) |

#### Queue payload models

| Model | Queue |
|---|---|
| `ScrapeJobQueueData` | `scrape-jobs` |
| `ProcessJobQueueData` | `process-jobs` |
| `ChunkJobQueueData` | `chunk-jobs` |
| `EmbedJobQueueData` | `embed-jobs` |
| `StoreJobQueueData` | `store-jobs` |

### Endpoints

#### `POST /jobs`

Submit a new scrape job.

Example request:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -H "x-modal-auth-key: $MODAL_AUTH_KEY" \
  -H "x-modal-auth-secret: $MODAL_AUTH_SECRET" \
  -d '{
    "url": "https://example.com",
    "user_id": "user-123",
    "crawl_config": {
      "max_depth": 2,
      "timeout_seconds": 120
    },
    "chunking_config": {
      "min_size_tokens": 256,
      "max_size_tokens": 1024,
      "overlap_ratio": 0.2
    },
    "metadata": {
      "source": "readme-example"
    }
  }'
```

Success response (`201`):

```json
{
  "job_id": "test-job-id-123",
  "status": "pending",
  "created_at": "2026-03-12T10:00:00.000000",
  "url": "https://example.com/"
}
```

Common errors:

- `422` validation error (invalid URL, missing `user_id`, invalid config bounds)
- `500` internal/database error

#### `GET /jobs/{job_id}`

Get current job status.

Example request:

```bash
curl http://localhost:8000/jobs/<job_id> \
  -H "x-modal-auth-key: $MODAL_AUTH_KEY" \
  -H "x-modal-auth-secret: $MODAL_AUTH_SECRET"
```

Response (`200`) maps to `JobStatusResponse`:

```json
{
  "job_id": "job-123",
  "status": "crawling",
  "progress_pct": 20,
  "current_step": "crawling",
  "error_message": null,
  "updated_at": "2026-03-12T10:05:00.000000",
  "created_at": "2026-03-12T10:00:00.000000",
  "crawl_url_count": 5,
  "chunk_count": 0,
  "embedding_count": 0
}
```

Common errors:

- `404` job not found
- `500` internal/database error

#### `GET /jobs`

List recent jobs with optional filter.

Query params:

- `user_id` (optional string)
- `limit` (optional integer, default `50`, valid range `1..100`)

Current response shape (`200`):

```json
{
  "user_id": null,
  "limit": 50,
  "jobs": [],
  "total": 0
}
```

Notes:

- This endpoint currently returns a placeholder list structure.
- Invalid `limit` returns `422`.

#### `POST /jobs/{job_id}/cancel`

Cancel a non-terminal job.

Example request:

```bash
curl -X POST http://localhost:8000/jobs/<job_id>/cancel \
  -H "x-modal-auth-key: $MODAL_AUTH_KEY" \
  -H "x-modal-auth-secret: $MODAL_AUTH_SECRET"
```

Success response (`200`):

```json
{
  "job_id": "job-123",
  "previous_status": "pending",
  "new_status": "cancelled"
}
```

Common errors:

- `404` job not found
- `409` cannot cancel terminal state (`completed`, `failed`, `cancelled`)
- `500` internal/database error

## Configuration

Environment variables are defined in `.env.example`.

### Required for local/runtime behavior

| Variable | Description |
|---|---|
| `SUPABASE_PROJECT_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Supabase service key |
| `VECINITA_EMBEDDING_API_URL` | Embedding API endpoint |

### Required for protected API access

| Variable | Description |
|---|---|
| `MODAL_AUTH_KEY` | Expected `x-modal-auth-key` value |
| `MODAL_AUTH_SECRET` | Expected `x-modal-auth-secret` value |

### Wired in GitHub Actions workflow

| Secret | Used by CI deploy job |
|---|---|
| `MODAL_TOKEN_ID` | Yes |
| `MODAL_TOKEN_SECRET` | Yes |
| `SUPABASE_PROJECT_URL` | Yes |
| `SUPABASE_ANON_KEY` | Yes |
| `SUPABASE_SERVICE_KEY` | Yes |
| `VECINITA_EMBEDDING_API_URL` | Yes |

### Optional configuration

| Variable | Purpose |
|---|---|
| `SUPABASE_PUBLISHABLE_KEY` | Optional client/publishable Supabase key |
| `MODAL_WORKSPACE` | Workspace naming/context |
| `MODAL_PROXY_AUTH_ENABLED` | Toggle proxy auth middleware |
| `VECINITA_MODEL_API_URL` | Optional model API endpoint |
| `VECINITA_EMBEDDING_API_TOKEN` | Optional auth token for embedding API |
| `CRAWL4AI_TIMEOUT_SECONDS` | Crawl timeout tuning |
| `CRAWL4AI_MAX_DEPTH` | Crawl depth tuning |
| `CHUNK_MIN_SIZE_TOKENS` | Chunk size lower bound tuning |
| `CHUNK_MAX_SIZE_TOKENS` | Chunk size upper bound tuning |
| `CHUNK_OVERLAP_RATIO` | Chunk overlap tuning |
| `LOG_LEVEL` | Logging verbosity |
| `ENVIRONMENT` | Runtime environment name |

## Development and Testing

```bash
# Format
make format

# Lint
make lint

# Type-check
make type-check

# Tests
make test
make test-unit
make test-integration
make test-live
make test-cov
```

Current automated test inventory:

- 16 unit tests
- 18 API tests
- 5 integration tests
- 39 total tests

## Deployment

- CI/CD runs on push/PR to `main`.
- Deployment job runs on push to `main` after tests.
- Deployment commands are:

```bash
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/app.py
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/api/app.py
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment details.

## Additional Documentation

- [QUICKSTART.md](QUICKSTART.md) - Fast setup and deploy flow
- [QUICKREF.md](QUICKREF.md) - Command quick reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment and CI/CD guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Readiness checklist
- [src/vecinita_scraper/core/models.py](src/vecinita_scraper/core/models.py) - Source-of-truth model definitions
- [src/vecinita_scraper/api/routes.py](src/vecinita_scraper/api/routes.py) - Source-of-truth route implementations

## License

MIT. See [LICENSE](LICENSE).