# vecinita-scraper

Serverless scraping pipeline for Vecinita.

## Current architecture

- FastAPI control plane served directly from Modal
- Queue-driven worker pipeline for scrape, process, chunk, embed, and store stages
- PostgreSQL-backed job state and document persistence
- Direct service-to-service calls to embedding and model endpoints

## Development

```bash
make dev-install
make test
make serve
```

`make test` and related test targets run with
`PYTHONWARNINGS=ignore:::requests` to suppress known non-blocking
`RequestsDependencyWarning` noise from `requests` import-time checks.

## Deployment

```bash
modal auth login
make deploy
```

### Render + Modal CLI (auth / secrets)

From the monorepo root, after `render login` and `modal` auth:

```bash
# Discover vecinita-data-management-api-v1 and dry-run PATCH of SCRAPER_API_KEYS from .env.prod.render
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --dry-run
export RENDER_API_KEY=...
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --yes

# Push / replace Modal secret vecinita-scraper-env (include all required keys in the file)
modal secret create vecinita-scraper-env --from-dotenv path/to/full-scraper-secret.env --force
# or the same via wrapper:
./scripts/sync_scraper_auth_render_modal.sh modal --from-dotenv path/to/full-scraper-secret.env --force
```

### Docker deploy

This service also ships with a Dockerfile and `render.yaml` for a Render Docker web-service deploy.

The root monorepo [`render.yaml`](../../render.yaml) injects `DATABASE_URL` for `vecinita-data-management-api-v1` from the single shared `vecinita-postgres` resource via `fromDatabase`. This directory’s [`render.yaml`](render.yaml) is for optional **standalone** Render deploys only: it does **not** provision a second database—set `DATABASE_URL` in the dashboard to your Postgres internal URL (or deploy from the repo root blueprint). If you run the same FastAPI image on **Modal**, add **`DATABASE_URL`**, **`SCRAPER_API_KEYS`**, upstream URLs, and CORS settings to the Modal secret group **`vecinita-scraper-env`** (see `vecinita_scraper.api.app`). GitHub Actions only supplies Modal CLI auth; it does not create or sync that secret’s keys for you. **Modal `DATABASE_URL` must point at the same active Render Postgres your blueprint uses** (update the secret after rotating or resuming databases); a stale DSN to a suspended instance causes `SSL connection has been closed unexpectedly` from Modal functions.

Required environment variables for the Docker / Render deployment:

- `DATABASE_URL`
- `SCRAPER_API_KEYS` — comma-separated Bearer secrets (or `DEV_ADMIN_BEARER_TOKEN` for one legacy token). **Omitting this in production causes immediate startup failure** (`ConfigError`).
- `VECINITA_EMBEDDING_API_URL`
- `CORS_ORIGINS`

Recommended environment variables:

- `VECINITA_MODEL_API_URL`
- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `MODAL_WORKSPACE`

Local image build:

```bash
docker build -t vecinita-data-management-api-v1 .
docker run --rm -p 10000:10000 \
	-e PORT=10000 \
	-e ENVIRONMENT=development \
	-e DATABASE_URL=postgresql://user:pass@host:5432/db \
	-e SCRAPER_API_KEYS=local-dev-key \
	-e VECINITA_EMBEDDING_API_URL=https://example-embedding.modal.run \
	-e CORS_ORIGINS=http://localhost:3000 \
	vecinita-data-management-api-v1
```

## Runtime requirements

- `DATABASE_URL` (canonical Postgres DSN)
- `DB_URL` (optional; used only if `DATABASE_URL` is empty)
- `DATABASE_URL` (canonical Postgres DSN)
- `DB_URL` (optional; used only if `DATABASE_URL` is empty, same string otherwise)
- `VECINITA_EMBEDDING_API_URL`
- `VECINITA_MODEL_API_URL` when model-assisted extraction is enabled
- Modal credentials for deploy operations

## API

The control plane exposes job endpoints under `/jobs`.

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs`
- `POST /jobs/{job_id}/cancel`
