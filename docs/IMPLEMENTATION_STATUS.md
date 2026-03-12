# Vecinita Scraper - Phase 1 & 2 Complete ✅

A serverless web scraping pipeline on Modal with job queue management, semantic document processing, and vector embeddings.

## 📋 Current Implementation Status

### ✅ Completed (Phase 1: Data Models & Phase 2: Modal Infrastructure)

**Phase 1: Data Models & Database Schema**
- [x] Pydantic models for API/queue communication (`core/models.py`)
  - `JobStatus` enum with 8-step pipeline (PENDING → COMPLETED/FAILED)
  - `ScrapeJobRequest`, `JobStatusResponse`, `ChunkWithEmbedding`
  - Queue data models for inter-worker communication
  - Configuration dataclasses
- [x] Custom exception hierarchy (`core/errors.py`)
- [x] Supabase schema migrations (`migrations/`)
  - `scraping_jobs` table with RLS policies
  - `crawled_urls`, `extracted_content`, `processed_documents`, `chunks`, `embeddings` tables
  - Proper foreign key relationships and indexes

**Phase 2: Modal Infrastructure**
- [x] Configuration loading (`core/config.py`)
  - Environment-based config for Supabase, Modal, APIs, Crawl4AI
  - Validation and caching
- [x] Structured logging (`core/logger.py`)
  - JSON structured logs via structlog
- [x] Supabase client wrapper (`core/db.py`)
  - CRUD operations for jobs, content, chunks, embeddings
  - Error handling and logging
- [x] Modal app initialization (`app.py`)
  - Queue definitions (scrape, process, chunk, embed, store)
  - Health check endpoint
- [x] Project structure and dependencies
  - `pyproject.toml` with production + dev dependencies
  - `.env.example` template
  - `Makefile` for common tasks

## 📁 Project Structure

```
vecinita-scraper/
├── src/vecinita_scraper/
│   ├── __init__.py
│   ├── app.py                     # Modal app with queues
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # ✅ Configuration loading
│   │   ├── db.py                  # ✅ Supabase wrapper
│   │   ├── errors.py              # ✅ Custom exceptions
│   │   ├── logger.py              # ✅ Structured logging
│   │   └── models.py              # ✅ Pydantic models
│   ├── crawlers/                  # Phase 3 (pending)
│   ├── processors/                # Phase 4 (pending)
│   ├── chunkers/                  # Phase 5 (pending)
│   ├── clients/                   # Phase 6 (pending)
│   ├── workers/                   # Phase 3-7 (pending)
│   └── api/                       # Phase 8 (pending)
├── tests/
│   ├── conftest.py                # ✅ Pytest fixtures
│   ├── unit/                      # Phase 10 (pending)
│   ├── integration/               # Phase 10 (pending)
│   ├── api/                       # Phase 10 (pending)
│   ├── smoke/                     # Phase 10 (pending)
│   └── e2e/                       # Phase 10 (pending)
├── migrations/                    # ✅ SQL migrations
│   ├── 001_create_scraping_jobs.sql
│   └── 002_create_content_tables.sql
├── docs/                          # Phase 12 (pending)
├── .github/workflows/             # Phase 11 (pending)
├── pyproject.toml                 # ✅ Dependencies
├── .env.example                   # ✅ Config template
└── Makefile                       # ✅ Development commands
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Development setup
make dev-install

# Or manual
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual values:
# - Supabase credentials
# - Modal credentials
# - API URLs
```

### 3. Set Up Database

Run migrations in Supabase SQL editor:

```bash
# 1. Enable pgvector extension (optional, for vector search)
# CREATE EXTENSION IF NOT EXISTS vector;

# 2. Run migrations from migrations/ directory
# Copy contents of 001_create_scraping_jobs.sql
# Copy contents of 002_create_content_tables.sql
```

Or use the Supabase Python client:

```python
from supabase import create_client
from src.vecinita_scraper.core.config import get_config

config = get_config()
client = create_client(config.supabase.project_url, config.supabase.service_key)

# Read and execute migration files
with open("migrations/001_create_scraping_jobs.sql") as f:
    client.postgrest.execute(f.read())
```

### 4. Verify Setup

```bash
# Lint code
make lint

# Type check
make type-check

# Run unit tests (once Phase 3+ are implemented)
make test-unit
```

## 📊 Database Schema

### Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `scraping_jobs` | Job tracking | id, url, user_id, status, created_at |
| `crawled_urls` | Raw crawled content | job_id, url, raw_content_hash, status |
| `extracted_content` | Extracted before processing | crawled_url_id, content_type, raw_content |
| `processed_documents` | After Docling processing | extracted_content_id, markdown_content, metadata |
| `chunks` | Semantic chunks | processed_doc_id, chunk_text, position, token_count |
| `embeddings` | Final vectors | chunk_id, embedding_vector (384-dim), model_name |

### Job Status Flow

```
PENDING → VALIDATING → CRAWLING → EXTRACTING → PROCESSING 
→ CHUNKING → EMBEDDING → STORING → COMPLETED
                                  ↓
                                FAILED (any stage)
                                  ↓
                                CANCELLED
```

## 🔄 Modal Queues

The worker pipeline uses Modal Queues for reliable inter-service communication:

1. **scrape-jobs** ← User submits via REST API
2. **process-jobs** ← Scraper emits crawled content
3. **chunk-jobs** ← Processor emits processed docs
4. **embed-jobs** ← Chunker emits chunks for embedding
5. **store-jobs** ← Embedder emits final results

Each queue is FIFO, persistent across worker restarts, and auto-scales consumers.

## 🛠️ Development Commands

```bash
# Code quality
make lint           # Ruff linter
make format         # Black + isort
make type-check     # mypy

# Testing
make test           # Unit + integration tests (no live)
make test-cov       # Coverage report (requires > 95%)
make test-live      # Hit real APIs

# Deployment
make deploy         # Deploy both workers and API to Modal
make serve          # Local development: `modal serve`

# Clean
make clean          # Remove build artifacts
```

## 📝 Configuration

See `.env.example` for all available configuration options:

- **Supabase**: Project URL, API keys
- **Modal**: Token ID/secret for authentication
- **Crawl4AI**: Timeout, max depth
- **Chunking**: Min/max token sizes, overlap ratio
- **APIs**: vecinita-model & embedding endpoints

## ⚠️ Notes

### Supabase Setup
- Make sure to enable the `pgvector` extension if using vector search
- RLS policies are set up but may need adjustment based on your auth setup
- Run migrations in Supabase SQL editor or via Python client

### Modal Secrets
Store credentials as Modal Secrets (not in code):
```bash
modal secret create vecinita-scraper \
  SUPABASE_PROJECT_URL=xxx \
  SUPABASE_SERVICE_KEY=xxx
```

## 🎯 Next Phases

- **Phase 3**: Crawl4AI adapter + scraper worker
- **Phase 4**: Docling processor worker
- **Phase 5**: Semantic chunking worker (with adaptive sizing)
- **Phase 6**: Embedding client + worker (with @modal.batched)
- **Phase 7**: Storage finalizer
- **Phase 8**: REST API + WebSocket
- **Phase 9**: Optional job scheduler
- **Phase 10**: Comprehensive tests (95%+ coverage)
- **Phase 11**: GitHub Actions CI/CD
- **Phase 12**: Documentation

## 📞 Support

For issues or questions:
1. Check `.env.example` for configuration
2. Review migrations for schema
3. Check `core/models.py` for data structures
4. Review error types in `core/errors.py`
