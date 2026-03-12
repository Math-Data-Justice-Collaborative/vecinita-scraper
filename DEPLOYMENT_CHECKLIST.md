# ✅ Deployment Readiness Checklist

Use this checklist to verify everything is ready before deploying to Modal.

## Pre-Deployment Checklist

### Environment Setup
- [ ] Modal CLI installed
  ```bash
  which modal && modal --version
  ```
  Expected: `/path/to/modal` and version info

- [ ] `.env` file exists and is configured
  ```bash
  ls -la .env
  ```
  Expected: File exists with Supabase and embedding API variables

- [ ] `.env` is in `.gitignore` (for security)
  ```bash
  grep ".env" .gitignore
  ```
  Expected: `.env` listed in .gitignore

### Modal Authentication  
- [ ] Modal credentials exist
  ```bash
  ls -la ~/.modal/
  ```
  Expected: Files `token_id` and `token_secret` present
  
  If missing:
  ```bash
  modal auth login
  ```

### Code Quality
- [ ] All tests pass
  ```bash
  pytest tests/ -v
  ```
  Expected: 
  - Unit tests: ✓ (14 passing)
  - API tests: ✓ (16 passing)
  - Integration tests: ✓ (5 passing)
  - **Total: 35 tests passing**

- [ ] Linting passes
  ```bash
  ruff check src/ tests/
  ```
  Expected: No errors (warnings OK)

- [ ] Type checking passes
  ```bash
  mypy src/ --ignore-missing-imports
  ```
  Expected: Success or acceptable warnings

### Code Structure Verification
- [ ] Workers Modal app exists
  ```bash
  test -f src/vecinita_scraper/app.py && echo "✓ Found"
  ```
  Expected: ✓ Found

- [ ] API Modal app exists
  ```bash
  test -f src/vecinita_scraper/api/app.py && echo "✓ Found"
  ```
  Expected: ✓ Found

- [ ] FastAPI server exists
  ```bash
  test -f src/vecinita_scraper/api/server.py && echo "✓ Found"
  ```
  Expected: ✓ Found

### Configuration Files
- [ ] GitHub Actions workflow exists
  ```bash
  test -f .github/workflows/ci-cd.yml && echo "✓ Found"
  ```
  Expected: ✓ Found

- [ ] Deployment script exists and is executable
  ```bash
  test -x scripts/deploy.sh && echo "✓ Executable"
  ```
  Expected: ✓ Executable

- [ ] Makefile has deploy targets
  ```bash
  grep "deploy:" Makefile
  ```
  Expected: Deploy commands present

### Documentation
- [ ] DEPLOYMENT.md exists
  ```bash
  test -f DEPLOYMENT.md && echo "✓ Found"
  ```
  Expected: ✓ Found

- [ ] QUICKSTART.md exists
  ```bash
  test -f QUICKSTART.md && echo "✓ Found"
  ```
  Expected: ✓ Found

- [ ] README.md has deployment info
  ```bash
  grep -i "deployment\|modal" README.md
  ```
  Expected: Deployment documentation present

## Local Deployment Test

Before GitHub Actions automation, test locally:

```bash
# 1. Verify environment
echo "Modal:" && which modal && modal --version
echo "Python:" && python --version
echo ".env:" && test -f .env && echo "✓ Found"

# 2. Run tests
pytest tests/ -q

# 3. Deploy to Modal (if tests pass)
./scripts/deploy.sh
# OR manually:
export PYTHONPATH=src
modal deploy src/vecinita_scraper/app.py
modal deploy src/vecinita_scraper/api/app.py
```

Expected output:
```
✓ Modal deployed to ...
✓ API deployed to ...
```

## GitHub Actions Setup

For automatic CI/CD, add secrets to GitHub:

```bash
# Go to: GitHub Settings → Secrets and variables → Actions
# Add these secrets from your local .env:
```

Required secrets:
- [ ] `MODAL_TOKEN_ID`
- [ ] `MODAL_TOKEN_SECRET`
- [ ] `SUPABASE_PROJECT_URL`
- [ ] `SUPABASE_ANON_KEY`
- [ ] `SUPABASE_SERVICE_KEY`
- [ ] `VECINITA_EMBEDDING_API_URL`

Once secrets are added:
```bash
git push origin main
```

Check deployment:
- [ ] GitHub Actions workflow triggers
- [ ] All tests pass (logs available in Actions tab)
- [ ] Apps deploy to Modal successfully
- [ ] Apps appear in Modal dashboard

## Post-Deployment Verification

After deployment:

```bash
# View deployed apps
modal app list

# Check app status
modal app info vecinita-scraper
modal app info vecinita-scraper-api

# View logs
modal logs -f vecinita-scraper
modal logs -f vecinita-scraper-api

# Test API (if deployed successfully)
curl https://YOUR_API_URL/docs
```

Expected:
- [ ] Both apps visible in Modal dashboard
- [ ] Workers app processing tasks
- [ ] API app serving requests
- [ ] Logs show no critical errors

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Modal not found | `pip install --upgrade modal` |
| Auth fails | `modal auth login` or set env vars |
| Tests fail | Check `.env` and logs, verify dependencies |
| Deployment fails | Review Modal logs: `modal logs <app>` |
| GitHub Actions fails | Add missing secrets, check workflow syntax |

## Quick Reference

```bash
# Copy this and run to verify everything
echo "=== Deployment Checklist ===" && \
which modal && modal --version && echo "✓ Modal CLI" && \
test -f .env && echo "✓ .env exists" && \
test -f src/vecinita_scraper/app.py && echo "✓ Workers app" && \
test -f src/vecinita_scraper/api/app.py && echo "✓ API app" && \
test -f .github/workflows/ci-cd.yml && echo "✓ GitHub Actions" && \
test -x scripts/deploy.sh && echo "✓ Deploy script" && \
echo "" && echo "=== Credentials ===" && \
ls -la ~/.modal/ 2>/dev/null && echo "✓ Modal auth" || echo "✗ Modal auth needed: modal auth login" && \
echo "" && echo "=== Ready to deploy! ===" && \
echo "Next: ./scripts/deploy.sh"
```

---

**Status Check:** Run the quick reference command to verify all prerequisites.

**Next Step:** Follow [QUICKSTART.md](QUICKSTART.md) to deploy!
