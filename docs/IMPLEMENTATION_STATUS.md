# Implementation Status

This document tracks the current implementation state for `vecinita-scraper`.

## Current State

The repository currently includes:

- FastAPI API app on Modal (`src/vecinita_scraper/api/app.py`)
- Worker app and queue pipeline on Modal (`src/vecinita_scraper/app.py`)
- Core data models and queue payload models (`src/vecinita_scraper/core/models.py`)
- Supabase-backed job persistence and status retrieval
- CI/CD workflow for test + deploy (`.github/workflows/ci-cd.yml`)

## API Surface (Implemented)

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs`
- `POST /jobs/{job_id}/cancel`
- `GET /health`

Auth behavior:

- Protected routes require `x-modal-auth-key` and `x-modal-auth-secret` when proxy auth is enabled.
- Public routes: `/health`, `/docs`, `/redoc`, `/openapi.json`.

## Data Model Coverage

Primary request/response models in `core/models.py`:

- `ScrapeJobRequest`
- `CrawlConfig`
- `ChunkingConfig`
- `JobStatusResponse`
- `JobStatus` enum

Pipeline queue payload models:

- `ScrapeJobQueueData`
- `ProcessJobQueueData`
- `ChunkJobQueueData`
- `EmbedJobQueueData`
- `StoreJobQueueData`

## Quality and Test Baseline

Current test inventory:

- 16 unit tests
- 18 API tests
- 5 integration tests
- 39 total tests

Supported quality gates:

- `make lint`
- `make type-check`
- `make test`

## Deployment State

Deployment commands are defined in `Makefile` and CI workflow:

```bash
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/app.py
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/api/app.py
```

CI behavior from `.github/workflows/ci-cd.yml`:

- test job on push/PR to `main`
- deploy job on push to `main` after tests pass

## References

- `README.md` (authoritative API request/response and model docs)
- `src/vecinita_scraper/core/models.py`
- `src/vecinita_scraper/api/routes.py`
- `DEPLOYMENT.md`
