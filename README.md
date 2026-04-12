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

## Deployment

```bash
modal auth login
make deploy
```

### Docker deploy

This service also ships with a Dockerfile and `render.yaml` for a Render Docker web-service deploy.

The root monorepo [`render.yaml`](../../render.yaml) injects `DATABASE_URL` for `vecinita-data-management-api-v1` from the single shared `vecinita-postgres` resource via `fromDatabase`. This directory’s [`render.yaml`](render.yaml) is for optional **standalone** Render deploys only: it does **not** provision a second database—set `DATABASE_URL` in the dashboard to your Postgres internal URL (or deploy from the repo root blueprint). If you run the same FastAPI image on **Modal**, add **`DATABASE_URL`** to the Modal secret group your deploy references so `vecinita_scraper` can validate and connect.

Required environment variables for the Docker deployment:

- `DATABASE_URL`
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
	-e DATABASE_URL=postgresql://user:pass@host:5432/db \
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
