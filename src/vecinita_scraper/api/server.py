"""FastAPI application with Modal ASGI integration."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vecinita_scraper.api.routes import router as jobs_router
from vecinita_scraper.core.logger import get_logger

logger = get_logger(__name__)


def _allowed_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    allowed_origins = _allowed_origins()

    app = FastAPI(
        title="Vecinita Scraper",
        description="Serverless web scraping pipeline with job queue management",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allowed_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any) -> Any:
        """Log HTTP requests."""
        logger.info("HTTP request", method=request.method, path=request.url.path)
        response = await call_next(request)
        logger.info(
            "HTTP response",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "service": "vecinita-scraper"}

    app.include_router(jobs_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions."""
        logger.exception("Unhandled exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
