"""FastAPI application with Modal ASGI integration."""

from __future__ import annotations

import os
import secrets
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vecinita_scraper.api.routes import router as jobs_router
from vecinita_scraper.core.logger import get_logger

logger = get_logger(__name__)

_AUTH_EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


def _is_proxy_auth_enabled() -> bool:
    enabled = os.getenv("MODAL_PROXY_AUTH_ENABLED", "true").strip().lower()
    return enabled in {"1", "true", "yes", "on"}


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    expected_auth_key = os.getenv("MODAL_AUTH_KEY", "").strip()
    expected_auth_secret = os.getenv("MODAL_AUTH_SECRET", "").strip()
    proxy_auth_required = _is_proxy_auth_enabled() and bool(
        expected_auth_key and expected_auth_secret
    )

    app = FastAPI(
        title="Vecinita Scraper",
        description="Serverless web scraping pipeline with job queue management",
        version="0.1.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any) -> Any:
        """Log HTTP requests."""
        if proxy_auth_required and request.url.path not in _AUTH_EXEMPT_PATHS:
            auth_key = request.headers.get("x-modal-auth-key", "")
            auth_secret = request.headers.get("x-modal-auth-secret", "")
            key_matches = secrets.compare_digest(auth_key, expected_auth_key)
            secret_matches = secrets.compare_digest(auth_secret, expected_auth_secret)
            is_valid = key_matches and secret_matches
            if not is_valid:
                logger.warning(
                    "Rejected request due to invalid modal proxy auth",
                    method=request.method,
                    path=request.url.path,
                )
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized"},
                )

        logger.info("HTTP request", method=request.method, path=request.url.path)
        response = await call_next(request)
        logger.info(
            "HTTP response",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "service": "vecinita-scraper"}

    # Include routers
    app.include_router(jobs_router)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions."""
        logger.exception("Unhandled exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


# Create the app instance
app = create_app()
