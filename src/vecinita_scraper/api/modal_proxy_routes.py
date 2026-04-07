"""Compatibility shim for legacy modal proxy route module.

This module existed historically and was removed when the scraper service moved
to direct job APIs backed by Postgres. It remains as a tracked file so editor
Git history lookups against this path continue to work and any stale imports
fail gracefully.
"""

from __future__ import annotations

from fastapi import APIRouter

# Keep the historical symbol name expected by older imports.
# Intentionally no routes are registered.
router = APIRouter(prefix="/modal", tags=["modal-proxy-legacy"])
