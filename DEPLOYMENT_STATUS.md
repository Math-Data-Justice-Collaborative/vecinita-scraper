# Deployment Status

Last updated: 2026-03-12

## Summary

Current deployment setup is operational and documented.

- Modal workers app: `src/vecinita_scraper/app.py`
- Modal API app: `src/vecinita_scraper/api/app.py`
- CI workflow: `.github/workflows/ci-cd.yml`

## Current API Surface

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs`
- `POST /jobs/{job_id}/cancel`
- `GET /health`
- `GET /docs`

Proxy auth behavior:

- Protected routes require `x-modal-auth-key` and `x-modal-auth-secret` when enabled.
- Public routes: `/health`, `/docs`, `/redoc`, `/openapi.json`.

## Test Baseline

Current test inventory:

- 16 unit tests
- 18 API tests
- 5 integration tests
- 39 total tests

## CI/CD Status

Workflow behavior:

- Test job runs on push and pull request to `main`
- Deploy job runs on push to `main` after test job

Workflow-wired secrets:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `SUPABASE_PROJECT_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VECINITA_EMBEDDING_API_URL`

## Deployment Commands

```bash
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/app.py
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/api/app.py
```

## Verification Commands

```bash
make test
make deploy
modal app list
```

## Related Documentation

- `README.md` (API request/response and model docs)
- `QUICKSTART.md`
- `QUICKREF.md`
- `DEPLOYMENT.md`
- `DEPLOYMENT_CHECKLIST.md`
