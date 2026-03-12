# vecinita-scraper

[![CI/CD - Deploy to Modal](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper/actions/workflows/ci-cd.yml)

A serverless web scraping pipeline with job queue management on Modal.

## Features

- **Distributed Job Queue**: Scalable architecture with Modal job queues
- **Multi-stage Pipeline**: Crawl → Process → Chunk → Embed → Finalize
- **Web Crawling**: Breadth-first site crawling with Crawl4AI
- **Document Processing**: HTML/PDF/DOCX processing with Docling
- **Semantic Chunking**: Token-aware text chunking for optimal embeddings
- **Embedding Integration**: Adaptive batch embedding with latency-based tuning
- **REST API**: FastAPI endpoints for job submission and status tracking
- **CI/CD**: Automatic deployment to Modal on push to main

## Quick Start

### Local Development

```bash
# Install dependencies
make dev-install

# Run tests
make test

# Serve locally
make serve
```

### Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick deploy:**
```bash
modal auth login  # Authenticate with Modal
make deploy
```

## Architecture

```
┌─────────────────┐
│   REST API      │  POST /jobs → Create job
│   (FastAPI)     │  GET /jobs/{id} → Check status
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Job Database   │  Supabase PostgreSQL
│  (Supabase)     │  Tracks job progress
└─────────────────┘

┌──────────────────────────────────────────────┐
│          Modal Worker Pipeline               │
├──────────────────────────────────────────────┤
│                                              │
│  Scraper Worker      Crawl4AI                │
│  ↓ scrape-jobs       ↓ BFS crawl             │
│  ↓ process-jobs                              │
│                                              │
│  Processor Worker    Docling                 │
│  ↓ chunk-jobs        ↓ HTML/PDF → Markdown   │
│                                              │
│  Chunker Worker      SemanticChunker         │
│  ↓ embed-jobs        ↓ Token-aware split     │
│                                              │
│  Embedder Worker     EmbeddingClient         │
│  ↓ store-jobs        ↓ Batch embed           │
│                                              │
│  Finalizer Worker    JobStatus               │
│  ↓ COMPLETED         ↓ Mark complete         │
│                                              │
└──────────────────────────────────────────────┘
```

## API Endpoints

### Submit a Job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -H "X-Modal-Auth-Key: $MODAL_AUTH_KEY" \
  -H "X-Modal-Auth-Secret: $MODAL_AUTH_SECRET" \
  -d '{
    "url": "https://example.com",
    "user_id": "user-123",
    "crawl_config": {
      "max_depth": 2,
      "timeout_seconds": 60
    }
  }'

# Response:
# {
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "pending",
#   "created_at": "2026-03-12T10:00:00"
# }
```

### Check Job Status
```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-Modal-Auth-Key: $MODAL_AUTH_KEY" \
  -H "X-Modal-Auth-Secret: $MODAL_AUTH_SECRET"

# Response:
# {
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "crawling",
#   "progress_pct": 20,
#   "current_step": "crawling",
#   "updated_at": "2026-03-12T10:05:00",
#   "crawl_url_count": 5,
#   "chunk_count": 0,
#   "embedding_count": 0
# }
```

### Cancel a Job
```bash
curl -X POST http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000/cancel \
  -H "X-Modal-Auth-Key: $MODAL_AUTH_KEY" \
  -H "X-Modal-Auth-Secret: $MODAL_AUTH_SECRET"

# Response:
# {
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "previous_status": "pending",
#   "new_status": "cancelled"
# }
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Required |
|---|---|---|
| `SUPABASE_PROJECT_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service key | Yes |
| `VECINITA_EMBEDDING_API_URL` | Embedding API endpoint | Yes |
| `MODAL_AUTH_KEY` | Proxy auth header key for API requests | Yes (for protected endpoints) |
| `MODAL_AUTH_SECRET` | Proxy auth header secret for API requests | Yes (for protected endpoints) |
| `MODAL_PROXY_AUTH_ENABLED` | Enable/disable proxy auth middleware (`true`/`false`) | No |
| `ENVIRONMENT` | `development`, `staging`, or `production` | No |

## Development

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make type-check

# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# Coverage report
make test-cov

# Clean build artifacts
make clean
```

## Testing

The project includes:
- **14 unit tests** - Testing individual components
- **16 API tests** - Testing REST endpoints
- **5 integration tests** - Testing full pipeline

Run tests with:
```bash
make test
```

## Deployment Status

Automatic deployment to Modal happens on every push to `main` branch after tests pass.

View deployment logs in the [Actions](../../actions) tab.

## Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [API Routes](src/vecinita_scraper/api/routes.py) - REST endpoint documentation
- [Worker Documentation](src/vecinita_scraper/workers/) - Job processing pipeline
- [Configuration](src/vecinita_scraper/core/config.py) - Configuration options

## License

MIT - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Create a feature branch
2. Run tests and lint checks
3. Submit a pull request

## Support

For issues, questions, or suggestions, please open an issue on GitHub.