# Deployment Readiness Checklist

Use this checklist before local or CI deployment.

## Environment and Auth

- [ ] Modal CLI available

```bash
which modal && modal --version
```

- [ ] Modal authentication is configured (`modal auth login` or token env vars)

```bash
ls -la ~/.modal/
```

- [ ] `.env` exists and is aligned with `.env.example`

```bash
test -f .env && echo ".env present"
```

- [ ] `.env` is ignored by git

```bash
grep -n "^\.env$" .gitignore
```

## Required Runtime Variables

- [ ] `SUPABASE_PROJECT_URL`
- [ ] `SUPABASE_ANON_KEY`
- [ ] `SUPABASE_SERVICE_KEY`
- [ ] `VECINITA_EMBEDDING_API_URL`

If proxy auth is enabled:

- [ ] `MODAL_AUTH_KEY`
- [ ] `MODAL_AUTH_SECRET`

## Quality Gates

- [ ] Lint passes

```bash
make lint
```

- [ ] Type checks pass

```bash
make type-check
```

- [ ] Tests pass

```bash
make test
```

Current expected totals:

- 16 unit
- 18 API
- 5 integration
- 39 total

## Deploy Commands

- [ ] Workers deploy command succeeds

```bash
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/app.py
```

- [ ] API deploy command succeeds

```bash
PYTHONPATH=src python -m modal deploy src/vecinita_scraper/api/app.py
```

Equivalent convenience command:

```bash
make deploy
```

## Post-Deploy Validation

- [ ] Modal apps are visible

```bash
modal app list
```

- [ ] Health endpoint returns 200

```bash
curl https://<api-base-url>/health
```

- [ ] Protected jobs endpoint enforces auth (when enabled)

```bash
curl https://<api-base-url>/jobs
curl https://<api-base-url>/jobs \
  -H "x-modal-auth-key: $MODAL_AUTH_KEY" \
  -H "x-modal-auth-secret: $MODAL_AUTH_SECRET"
```

## GitHub Actions (CI/CD)

Workflow file: `.github/workflows/ci-cd.yml`

- [ ] Repository secrets configured:
  - `MODAL_TOKEN_ID`
  - `MODAL_TOKEN_SECRET`
  - `SUPABASE_PROJECT_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_KEY`
  - `VECINITA_EMBEDDING_API_URL`

Verify quickly:

```bash
gh secret list
```

## API Contract Sanity

- [ ] Endpoint set matches implementation:
  - `POST /jobs`
  - `GET /jobs/{job_id}`
  - `GET /jobs`
  - `POST /jobs/{job_id}/cancel`
  - `GET /health`
  - `GET /docs`

- [ ] Request/response schema docs are up-to-date in `README.md`
