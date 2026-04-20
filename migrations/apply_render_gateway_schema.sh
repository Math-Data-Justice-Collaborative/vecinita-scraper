#!/usr/bin/env bash
# Apply render_gateway_scraper_schema.sql to the database in DATABASE_URL.
# Run from repo root or any cwd (script resolves SQL path relative to this file).
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required (e.g. from Render dashboard or gateway env)." >&2
  exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL="${HERE}/render_gateway_scraper_schema.sql"

exec psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$SQL"
