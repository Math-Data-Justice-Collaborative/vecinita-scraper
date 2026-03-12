# 🚀 Quick Start: Modal Deployment

## Step 1: Authenticate with Modal

If you haven't authenticated with Modal yet, run:

```bash
modal auth login
```

This will:
- Open a browser to Modal's authentication page
- Create a token for your account
- Save credentials to `~/.modal/token_id` and `~/.modal/token_secret`

**Alternative: Use Environment Variables**

If you're in an environment where browser login isn't possible (e.g., CI/CD):

```bash
export MODAL_TOKEN_ID="your-token-id"
export MODAL_TOKEN_SECRET="your-token-secret"
```

Get your token from: https://modal.com/account/tokens

## Step 2: Configure Environment Variables

Create a `.env` file in the project root with required secrets:

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `SUPABASE_PROJECT_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_KEY` - Supabase service role key (for secure operations)
- `VECINITA_EMBEDDING_API_URL` - Your embedding API endpoint

> ⚠️ **Never commit `.env` to version control!** It's in `.gitignore`.

## Step 3: Deploy Locally

Test deployment on your machine:

```bash
# Option A: Use the deployment script
./scripts/deploy.sh

# Option B: Manual deployment
export PYTHONPATH=src
pytest tests/unit tests/integration  # Verify tests pass
modal deploy src/vecinita_scraper/app.py
modal deploy src/vecinita_scraper/api/app.py
```

The script will:
1. ✓ Verify Modal credentials exist
2. ✓ Load environment from `.env`
3. ✓ Run all unit and integration tests
4. ✓ Deploy workers app to Modal
5. ✓ Deploy API app to Modal

## Step 4: Set Up GitHub Actions (Optional)

For automatic deployment on every push to main:

1. Go to your GitHub repository
2. Navigate to **Settings → Secrets and variables → Actions**
3. Add these secrets:

| Secret Name | Value |
|---|---|
| `MODAL_TOKEN_ID` | Token ID from Modal account |
| `MODAL_TOKEN_SECRET` | Token secret from Modal account |
| `SUPABASE_PROJECT_URL` | From your `.env` |
| `SUPABASE_ANON_KEY` | From your `.env` |
| `SUPABASE_SERVICE_KEY` | From your `.env` |
| `VECINITA_EMBEDDING_API_URL` | From your `.env` |

Once secrets are added:
```bash
git push origin main
```

GitHub Actions will automatically:
- Run all tests
- Deploy both apps to Modal (if tests pass)
- Provide deployment logs

## Step 5: Verify Deployment

Check if apps are deployed:

```bash
# List all deployed apps
modal app list

# View logs
modal logs vecinita-scraper
modal logs vecinita-scraper-api

# Check status
modal status

# Get app URLs
modal app info vecinita-scraper
modal app info vecinita-scraper-api
```

## Common Commands

```bash
# Deploy just the workers
modal deploy src/vecinita_scraper/app.py

# Deploy just the API
modal deploy src/vecinita_scraper/api/app.py

# Run tests
pytest tests/ -v

# View recent deployments
modal deployment list

# Tail logs from an app
modal logs -f vecinita-scraper-api

# Stop an app
modal app stop vecinita-scraper
modal app stop vecinita-scraper-api
```

## Troubleshooting

### Modal command not found
```bash
# Install or upgrade Modal
pip install --upgrade modal

# Verify installation
which modal
modal --version
```

### Authentication fails
```bash
# Re-authenticate
rm -rf ~/.modal
modal auth login
```

### Deployment fails - "No credentials found"
- Check: `ls -la ~/.modal/` should have `token_id` and `token_secret`
- Or: Set `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` environment variables
- Get tokens from: https://modal.com/account/tokens

### Tests fail before deployment
- Review test output and error messages
- Check `.env` has all required variables
- Ensure Supabase project is accessible

## Architecture

The project has two separate Modal apps:

**1. Workers App** (`src/vecinita_scraper/app.py`)
- Runs scraping tasks asynchronously
- Uses Modal queues for task distribution
- Integrates Crawl4AI, Docling, and semantic chunking

**2. API App** (`src/vecinita_scraper/api/app.py`)
- Serves REST API endpoints
- FastAPI application wrapped in Modal ASGI
- Provides endpoints for:
  - `POST /scrape` - Scrape URLs asynchronously
  - `GET /results/{task_id}` - Fetch scraping results
  - `GET /status/{task_id}` - Check task status
  - `GET /docs` - Swagger documentation

## Documentation

For more details, see:
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Comprehensive deployment guide
- [Modal Documentation](https://modal.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## Need Help?

- Check logs: `modal logs -f <app-name>`
- Review GitHub Actions: https://github.com/YOUR_REPO/actions
- Read error messages carefully
- See [DEPLOYMENT.md](../DEPLOYMENT.md) troubleshooting section

---

**Ready to deploy?** Start with Step 1 above!
