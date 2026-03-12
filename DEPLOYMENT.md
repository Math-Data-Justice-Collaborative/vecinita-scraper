# Deployment Guide

This guide covers deploying the Vecinita Scraper to Modal with GitHub Actions CI/CD.

## Prerequisites

- Modal CLI installed: `pip install modal`
- Modal account created at https://modal.com
- GitHub repository with secrets configured

## Local Deployment

### 1. Set up Modal

```bash
# Authenticate with Modal
modal token new

# This creates credentials at ~/.modal/token_id and ~/.modal/token_secret
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with:

```env
SUPABASE_PROJECT_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
VECINITA_EMBEDDING_API_URL=https://your-embedding-api.com
```

### 3. Deploy Locally

**Deploy workers and queues:**
```bash
make deploy
# Or manually:
PYTHONPATH=src python3 -m modal deploy src/vecinita_scraper/app.py
```

**Deploy API:**
```bash
PYTHONPATH=src python3 -m modal deploy src/vecinita_scraper/api/app.py
```

**Serve locally (for development):**
```bash
make serve
# Or manually:
PYTHONPATH=src python3 -m modal serve src/vecinita_scraper/api/app.py
```

## GitHub Actions CI/CD Setup

### 1. Create Modal Token

1. Go to https://modal.com/settings/tokens
2. Click "Create token"
3. Copy the token ID and secret

### 2. Add GitHub Secrets

Go to your GitHub repository > Settings > Secrets and variables > Actions

Add the following secrets:

| Secret Name | Value |
|---|---|
| `MODAL_TOKEN_ID` | Your Modal token ID |
| `MODAL_TOKEN_SECRET` | Your Modal token secret |
| `SUPABASE_PROJECT_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service key (for backend ops) |
| `VECINITA_EMBEDDING_API_URL` | Your embedding API endpoint |

### 3. Verify Workflow

The `.github/workflows/ci-cd.yml` workflow:
- Runs on every push to `main` branch
- Runs unit and integration tests
- Deploys to Modal if tests pass

To verify:
1. Push a commit to `main`
2. Go to Actions tab in GitHub
3. Watch the deployment progress

## Monitoring Deployments

### Modal Dashboard

View your deployed apps at https://modal.com/apps

**Workers App** - Job processing pipeline
- View logs: `modal logs`
- Check status: `modal status`

**API App** - REST endpoints
- Access at the provided Modal URL
- Check endpoint: `curl https://your-modal-url/health`

### GitHub Actions

Monitor deployments in the Actions tab of your GitHub repository.

View logs by clicking on completed workflow runs.

## Troubleshooting

### Deployment Fails

Check the GitHub Actions logs for error details.

Common issues:
- **Authentication failed**: Verify `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` are correct
- **Dependency errors**: Ensure all dependencies are in `pyproject.toml`
- **Env var missing**: Check all `SUPABASE_*` secrets are set

### Tests Failing

The workflow will not deploy if tests fail. To debug:

1. Run tests locally: `make test`
2. Fix any failures
3. Push to trigger workflow again

### Workers Not Starting

Check Modal logs:
```bash
modal logs <app-name>
```

Ensure all workers are properly imported in `src/vecinita_scraper/app.py`.

## Manual Deployment (Without CI/CD)

If you need to deploy without GitHub Actions:

```bash
# Export Modal credentials
export MODAL_TOKEN_ID=your-token-id
export MODAL_TOKEN_SECRET=your-token-secret

# Export environment variables
export SUPABASE_PROJECT_URL=...
export SUPABASE_ANON_KEY=...
export SUPABASE_SERVICE_KEY=...
export VECINITA_EMBEDDING_API_URL=...

# Deploy
make deploy
```

## Environment Configuration

The app reads configuration from environment variables:

- `SUPABASE_PROJECT_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Public API key
- `SUPABASE_SERVICE_KEY` - Service role key (for backend)
- `VECINITA_EMBEDDING_API_URL` - Embedding service endpoint
- `ENVIRONMENT` - "development", "staging", or "production"

See `src/vecinita_scraper/core/config.py` for full configuration details.

## Production Checklist

Before deploying to production:

- [ ] All tests passing locally
- [ ] Modal credentials set in GitHub Secrets
- [ ] All environment variables configured
- [ ] Supabase backup created
- [ ] Rate limiting configured (if needed)
- [ ] Monitoring/alerting set up
- [ ] API documentation reviewed
- [ ] Error handling tested

## Architecture

```
GitHub Actions (on push to main)
  ↓
Run tests (unit + integration)
  ↓
If tests pass:
  ├─ Deploy workers app → Modal app
  └─ Deploy API app → Modal web endpoint
  
Users access API at: https://<modal-url>/jobs
```

## Support

For issues:
1. Check GitHub Actions logs
2. Check Modal dashboard logs
3. Review environment variable configuration
4. Run tests locally to reproduce issues
