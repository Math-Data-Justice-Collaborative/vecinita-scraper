# Quick Start: Modal Deployment

This guide gets you from clone to deployed app quickly with commands that match the current repository state.

## 1) Authenticate With Modal

```bash
modal auth login
```

Alternative for non-interactive environments:

```bash
export MODAL_TOKEN_ID="your-token-id"
export MODAL_TOKEN_SECRET="your-token-secret"
```

## 2) Configure Environment

```bash
cp .env.example .env
```

Required values in `.env`:

- `SUPABASE_PROJECT_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VECINITA_EMBEDDING_API_URL`
- `MODAL_AUTH_KEY` and `MODAL_AUTH_SECRET` if API proxy auth is enabled

## 3) Install and Test

```bash
make dev-install
make lint
make type-check
make test
```

Current test inventory: 39 total (`16 unit`, `18 API`, `5 integration`).

## 4) Deploy

Fast path:

```bash
make deploy
```

Manual equivalent:

```bash
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/app.py
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/api/app.py
```

## 5) Verify

```bash
modal app list
modal app info vecinita-scraper
modal app info vecinita-scraper-api
```

Smoke checks:

```bash
# Public health endpoint
curl https://<api-base-url>/health

# Protected endpoint (when proxy auth enabled)
curl https://<api-base-url>/jobs \
  -H "x-modal-auth-key: $MODAL_AUTH_KEY" \
  -H "x-modal-auth-secret: $MODAL_AUTH_SECRET"
```

## API Endpoints (Current)

- `POST /jobs` - Submit a scraping job
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List jobs (currently placeholder list response)
- `POST /jobs/{job_id}/cancel` - Cancel a job
- `GET /health` - Health check (public)
- `GET /docs` - OpenAPI Swagger UI (public)

## GitHub Actions Setup

Workflow file: `.github/workflows/ci-cd.yml`

Required repository secrets for deploy job:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `SUPABASE_PROJECT_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VECINITA_EMBEDDING_API_URL`

Trigger behavior:

- Tests run on push and pull request to `main`
- Deploy runs on push to `main` after tests

## Troubleshooting

### Modal CLI not found

```bash
pip install --upgrade modal
modal --version
```

### Auth errors

```bash
modal auth login
```

### Deployment auth token missing in CI

Confirm GitHub secrets exist:

```bash
gh secret list
```

### Test failures

```bash
make test
```

## Next Reads

- [README.md](README.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [QUICKREF.md](QUICKREF.md)
