# Deployment Guide

This guide documents the current deployment workflow for this repository.

## Prerequisites

- Python 3.11+
- Modal CLI installed (`pip install modal`)
- Modal account and credentials
- `.env` configured from `.env.example`

## 1) Authenticate to Modal

Interactive:

```bash
modal auth login
```

Non-interactive alternative:

```bash
export MODAL_TOKEN_ID="your-token-id"
export MODAL_TOKEN_SECRET="your-token-secret"
```

## 2) Configure Environment

```bash
cp .env.example .env
```

Required runtime variables:

- `SUPABASE_PROJECT_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VECINITA_EMBEDDING_API_URL`

Required for protected API access (when proxy auth enabled):

- `MODAL_AUTH_KEY`
- `MODAL_AUTH_SECRET`

Optional variables are documented in `.env.example`.

## 3) Run Quality Gates Locally

```bash
make lint
make type-check
make test
```

Current baseline: 39 tests total (`16 unit`, `18 API`, `5 integration`).

## 4) Deploy

Primary command:

```bash
make deploy
```

Manual equivalent:

```bash
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/app.py
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/api/app.py
```

Local API serve:

```bash
make serve
```

## 5) Verify Deployment

```bash
modal app list
modal app info vecinita-scraper
modal app info vecinita-scraper-api
```

API checks:

```bash
curl https://<api-base-url>/health
curl https://<api-base-url>/jobs \
  -H "x-modal-auth-key: $MODAL_AUTH_KEY" \
  -H "x-modal-auth-secret: $MODAL_AUTH_SECRET"
```

## GitHub Actions CI/CD

Workflow file: `.github/workflows/ci-cd.yml`

Trigger behavior:

- Test job runs on push and pull request to `main`
- Deploy job runs on push to `main` after test job

Required GitHub repository secrets:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `SUPABASE_PROJECT_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VECINITA_EMBEDDING_API_URL`

Monitor runs in GitHub Actions.

## API Endpoints (Current)

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs`
- `POST /jobs/{job_id}/cancel`
- `GET /health`
- `GET /docs`

Full request/response schema details are maintained in `README.md`.

## Troubleshooting

### Token/authentication errors

- Re-run `modal auth login`
- Confirm CI secrets with `gh secret list`

### Missing environment values

- Check `.env` against `.env.example`
- Confirm CI secrets match deploy workflow requirements

### Test failures block deploy

```bash
make test
```

### Runtime issues

```bash
modal logs -f vecinita-scraper
modal logs -f vecinita-scraper-api
```

## Related Docs

- `README.md` (API schema and data model reference)
- `QUICKSTART.md`
- `QUICKREF.md`
- `DEPLOYMENT_CHECKLIST.md`
