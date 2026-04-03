"""Authenticated proxy routes for forwarding requests to Modal service endpoints."""

from __future__ import annotations

import os
from typing import Final

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status

from vecinita_scraper.core.config import get_config
from vecinita_scraper.core.logger import get_logger

router = APIRouter(prefix="/modal", tags=["modal-proxy"])
logger = get_logger(__name__)

_SUPPORTED_SERVICES: Final[set[str]] = {"embedding", "model"}
_ALLOWED_METHODS: Final[set[str]] = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _resolve_service_base_url(service: str) -> str:
    config = get_config()
    mapping = {
        "embedding": config.api.vecinita_embedding_api_url,
        "model": config.api.vecinita_model_api_url,
    }
    base_url = mapping.get(service, "").strip()
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No upstream URL configured for service '{service}'",
        )
    return base_url.rstrip("/")


def _build_upstream_headers(
    service: str, content_type: str | None, accept: str | None
) -> dict[str, str]:
    """Build headers for upstream service requests without forwarding auth tokens."""
    _ = service
    headers: dict[str, str] = {}
    if content_type:
        headers["content-type"] = content_type
    if accept:
        headers["accept"] = accept

    return headers


def _build_upstream_url(base_url: str, upstream_path: str) -> str:
    sanitized = upstream_path.lstrip("/")
    if not sanitized:
        return f"{base_url}/"
    return f"{base_url}/{sanitized}"


async def _forward_request(service: str, upstream_path: str, request: Request) -> Response:
    if service not in _SUPPORTED_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unsupported modal service '{service}'",
        )

    method = request.method.upper()
    if method not in _ALLOWED_METHODS:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Method '{method}' is not supported by modal proxy",
        )

    base_url = _resolve_service_base_url(service)
    upstream_url = _build_upstream_url(base_url, upstream_path)
    body = await request.body()
    query_params = dict(request.query_params)
    upstream_headers = _build_upstream_headers(
        service,
        request.headers.get("content-type"),
        request.headers.get("accept"),
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upstream_response = await client.request(
                method=method,
                url=upstream_url,
                params=query_params,
                content=body if body else None,
                headers=upstream_headers,
            )
    except httpx.RequestError as exc:
        logger.exception(
            "Modal proxy upstream request failed",
            service=service,
            method=method,
            url=upstream_url,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach upstream modal endpoint",
        ) from exc

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_response.headers.get("content-type"),
    )


@router.api_route("/{service}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_modal_service_root(service: str, request: Request) -> Response:
    """Proxy requests to a configured Modal service root endpoint."""
    return await _forward_request(service, "", request)


@router.api_route(
    "/{service}/{upstream_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_modal_service_path(service: str, upstream_path: str, request: Request) -> Response:
    """Proxy requests to a configured Modal service path endpoint."""
    return await _forward_request(service, upstream_path, request)
