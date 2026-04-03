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


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
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
