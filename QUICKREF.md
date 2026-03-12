# 🚀 Deployment Quick Reference

## TL;DR - Get Running in 3 Steps

### Step 1: Authenticate (5 min)
```bash
modal auth login
```

### Step 2: Test & Deploy (10 min)
```bash
./scripts/deploy.sh
```

### Step 3: Verify (5 min)
```bash
modal app list
```

---

## Common Commands

### Viewing & Monitoring
```bash
# List all deployed apps
modal app list

# Get app details
modal app info vecinita-scraper
modal app info vecinita-scraper-api

# View live logs
modal logs -f vecinita-scraper
modal logs -f vecinita-scraper-api

# View deployment history
modal deployment list

# Check app status
modal status
```

### Deployment
```bash
# Deploy everything (with tests)
./scripts/deploy.sh

# Deploy just workers app
PYTHONPATH=src modal deploy src/vecinita_scraper/app.py

# Deploy just API app
PYTHONPATH=src modal deploy src/vecinita_scraper/api/app.py

# Using Makefile
make deploy
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit -v
pytest tests/api -v
pytest tests/integration -v

# Run with coverage
pytest tests/ --cov=src
```

### Credentials
```bash
# Setup authentication
modal auth login

# Reset credentials
rm -rf ~/.modal
modal auth login

# Check token status
ls -la ~/.modal/
```

### Environment
```bash
# Create .env from template
cp .env.example .env

# Verify environment is loaded
export $(cat .env | xargs)

# Check Modal CLI version
modal --version
```

---

## GitHub Actions (CI/CD)

### One-Time Setup
1. Go to: **GitHub Repo → Settings → Secrets and variables → Actions**
2. Add these GitHub Secrets:
   ```
   MODAL_TOKEN_ID=<from your account>
   MODAL_TOKEN_SECRET=<from your account>
   SUPABASE_PROJECT_URL=<from .env>
   SUPABASE_ANON_KEY=<from .env>
   SUPABASE_SERVICE_KEY=<from .env>
   VECINITA_EMBEDDING_API_URL=<from .env>
   ```

### Automatic Deployment
```bash
# Just push to main - everything happens automatically!
git push origin main
```

Workflow runs:
1. Tests all code
2. Deploys to Modal if tests pass
3. Provides deployment log

### Monitor Workflow
- Go to: **GitHub Repo → Actions tab**
- Click on latest workflow run
- View logs and deployment status

---

## Troubleshooting

### "modal: command not found"
```bash
pip install --upgrade modal
```

### "Error: No credentials found"
```bash
modal auth login
# OR set environment variables:
export MODAL_TOKEN_ID=your-token
export MODAL_TOKEN_SECRET=your-secret
```

### "Tests failing"
```bash
# Check environment
cat .env

# Run tests with verbose output
pytest tests/ -v --tb=long

# Check dependencies
pip install -r requirements.txt
```

### "Deployment stuck"
```bash
# View logs
modal logs -f vecinita-scraper

# Check app status
modal status

# Force stop and redeploy
modal app stop vecinita-scraper
./scripts/deploy.sh
```

### "GitHub Actions failing"
1. Check all 6 secrets are set correctly
2. Verify .env is in .gitignore
3. Review Actions tab logs
4. Ensure local deployment works first

---

## Infrastructure Endpoints

After deployment, your apps are available at:

### Workers App
- **Name:** `vecinita-scraper`
- **Type:** Modal background worker
- **Tasks:** URL scraping, processing, chunking, embedding
- **Logs:** `modal logs -f vecinita-scraper`

### API App  
- **Name:** `vecinita-scraper-api`
- **Type:** Modal ASGI (FastAPI)
- **Base URL:** `https://your-workspace.modal.run/vecinita-scraper-api`
- **Endpoints:**
  - `GET /` - Welcome page
  - `GET /docs` - Swagger documentation
  - `GET /health` - Health check
  - `POST /submit_job` - Submit scraping job
  - `GET /job/{job_id}/status` - Check job status
  - `GET /job/{job_id}/results` - Get results
  - `POST /job/{job_id}/cancel` - Cancel job
- **Logs:** `modal logs -f vecinita-scraper-api`

---

## File Locations

```
Project Structure:
├── src/vecinita_scraper/
│   ├── app.py                 ← Workers Modal app
│   ├── api/
│   │   ├── app.py            ← API Modal wrapper
│   │   └── server.py         ← FastAPI server
│   └── [core modules]
├── scripts/
│   └── deploy.sh             ← Deployment script
├── .github/workflows/
│   └── ci-cd.yml             ← GitHub Actions
├── .env                       ← Your secrets (in .gitignore)
├── .env.example               ← Template
├── QUICKSTART.md              ← Getting started
├── DEPLOYMENT.md              ← Full guide
├── DEPLOYMENT_CHECKLIST.md    ← Verification
└── DEPLOYMENT_STATUS.md       ← This status report
```

---

## Documentation Map

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **This page** | Quick reference | Everyday use |
| [QUICKSTART.md](QUICKSTART.md) | Step-by-step setup | Getting started |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Comprehensive guide | Deep dive |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Verification | Before deploying |
| [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) | Project status | Overview |

---

## Quick Health Check

Verify everything is working:

```bash
cd /root/GitHub/VECINA/vecinita-scraper

# Check CLI
which modal && modal --version

# Check files
ls -la .env src/vecinita_scraper/app.py src/vecinita_scraper/api/app.py

# Check tests
pytest tests/ -q

# Check credentials
ls -la ~/.modal/

# Check GitHub Actions
ls -la .github/workflows/ci-cd.yml
```

Expected output:
```
✓ Modal CLI installed (v1.3.4+)
✓ All files exist
✓ 35 tests passing
✓ Credentials configured (or "Not set up yet")
✓ GitHub Actions workflow exists
```

---

## Deployment Timeline

```
Just Authenticated?
    ↓
    Deploy Locally: ./scripts/deploy.sh (10 min)
    ↓
Tests Passing + Apps Running?
    ↓
    Set GitHub Secrets (5 min)
    ↓
    Push to main (automatic deployment)
    ↓
Check GitHub Actions (5 min)
    ↓
✅ All Done! Apps auto-deploy on every push
```

---

## Need Help?

1. **Quick question?** Check this file
2. **Setup help?** See [QUICKSTART.md](QUICKSTART.md)
3. **Detailed info?** Read [DEPLOYMENT.md](DEPLOYMENT.md)
4. **Checking status?** Use the checklist [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
5. **Project overview?** See [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)

---

## Pro Tips

✨ **Best Practices:**
- Always run tests locally first
- Use `.env` for sensitive data (never push)
- Check logs after deployment
- Test API endpoints in Swagger at `/docs`
- Monitor GitHub Actions on every push
- Keep Modal credentials secure

⚡ **Speed Tips:**
- Use `make deploy` for quick deployment
- Use `./scripts/deploy.sh` for full process
- Watch logs with `modal logs -f <app-name>`
- Monitor with `modal status`

🔒 **Security Tips:**
- Never commit `.env` file
- Rotate Modal tokens regularly
- Use GitHub Secrets for CI/CD
- Keep Modal CLI updated

---

**Ready?** Run `modal auth login` → `./scripts/deploy.sh` → Done! 🚀
