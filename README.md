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

## Runtime requirements

- `DATABASE_URL`
- `VECINITA_EMBEDDING_API_URL`
- `VECINITA_MODEL_API_URL` when model-assisted extraction is enabled
- Modal credentials for deploy operations

## API

The control plane exposes job endpoints under `/jobs`.

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs`
- `POST /jobs/{job_id}/cancel`
