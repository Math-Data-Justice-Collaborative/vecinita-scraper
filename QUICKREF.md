# Deployment Quick Reference

## Fast Path

```bash
modal auth login
cp .env.example .env
make dev-install
make test
make deploy
```

## Core Commands

### Development

```bash
make lint
make type-check
make test
make test-unit
make test-integration
make test-live
```

### Deployment

```bash
# Deploy both workers + API
make deploy

# Deploy workers only
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/app.py

# Deploy API only
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/api/app.py

# Serve API locally with Modal
make serve
```

### Modal Observability

```bash
modal app list
modal app info vecinita-scraper
modal app info vecinita-scraper-api
modal logs -f vecinita-scraper
modal logs -f vecinita-scraper-api
```

## Current API Contract

Base path: `/jobs`

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs`
- `POST /jobs/{job_id}/cancel`

Public endpoints:

- `GET /health`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`

## Auth Headers (Protected Endpoints)

```http
x-modal-auth-key: <MODAL_AUTH_KEY>
x-modal-auth-secret: <MODAL_AUTH_SECRET>
```

Auth is enforced when:

- `MODAL_PROXY_AUTH_ENABLED=true`
- both `MODAL_AUTH_KEY` and `MODAL_AUTH_SECRET` are configured

## API Request/Response Shape (Quick)

### Submit Job

`POST /jobs`

Request body:

```json
{
    "url": "https://example.com",
    "user_id": "user-123",
    "crawl_config": {
        "max_depth": 3,
        "timeout_seconds": 60
    },
    "chunking_config": {
        "min_size_tokens": 256,
        "max_size_tokens": 1024,
        "overlap_ratio": 0.2
    },
    "metadata": {
        "source": "quickref"
    }
}
```

Response (`201`):

```json
{
    "job_id": "...",
    "status": "pending",
    "created_at": "...",
    "url": "https://example.com/"
}
```

### Get Job Status

`GET /jobs/{job_id}`

Response (`200`):

```json
{
    "job_id": "...",
    "status": "crawling",
    "progress_pct": 20,
    "current_step": "crawling",
    "error_message": null,
    "updated_at": "...",
    "created_at": "...",
    "crawl_url_count": 0,
    "chunk_count": 0,
    "embedding_count": 0
}
```

### Cancel Job

`POST /jobs/{job_id}/cancel`

Response (`200`):

```json
{
    "job_id": "...",
    "previous_status": "pending",
    "new_status": "cancelled"
}
```

## Test Inventory

- 16 unit tests
- 18 API tests
- 5 integration tests
- 39 total

## GitHub Actions Secrets

Workflow: `.github/workflows/ci-cd.yml`

Required for deploy job:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `SUPABASE_PROJECT_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VECINITA_EMBEDDING_API_URL`

## Troubleshooting

### Missing Modal auth

```bash
modal auth login
```

### CI deployment token errors

```bash
gh secret list
```

### Run the same checks as CI

```bash
ruff check src/ tests/
black --check src/ tests/
pytest tests/unit/ -v --tb=short
pytest tests/integration/ -v --tb=short
```

## See Also

- [README.md](README.md)
- [QUICKSTART.md](QUICKSTART.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
