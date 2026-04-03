"""Client for the Vecinita embedding API."""

from __future__ import annotations

from time import monotonic
from typing import Any, cast

from vecinita_scraper.core.config import get_config
from vecinita_scraper.core.errors import EmbeddingError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import EmbeddingModelConfig

logger = get_logger(__name__)


class EmbeddingClient:
    """Async client for fetching model metadata and embedding text batches."""

    def __init__(self, base_url: str | None = None, api_token: str | None = None) -> None:
        if base_url is None:
            config = get_config()
            resolved_base_url = base_url or config.api.vecinita_embedding_api_url
        else:
            resolved_base_url = base_url

        if not resolved_base_url:
            raise EmbeddingError("Missing required API configuration: VECINITA_EMBEDDING_API_URL")

        self._base_url = resolved_base_url.rstrip("/")
        _ = api_token  # Auth tokens are intentionally not forwarded from scraper clients.
        self._cached_model_config: EmbeddingModelConfig | None = None
        self._cache_time = 0.0
        self._default_batch_size = 100
        self._current_batch_size = 100

    async def fetch_embedding_model_config(
        self, force_refresh: bool = False
    ) -> EmbeddingModelConfig:
        """Fetch and cache embedding model metadata from the service root."""
        if (
            not force_refresh
            and self._cached_model_config
            and monotonic() - self._cache_time < 3600
        ):
            return self._cached_model_config

        response_json = await self._request("GET", "/")
        model_name = (
            response_json.get("model")
            or response_json.get("active_model")
            or "BAAI/bge-small-en-v1.5"
        )
        dimensions = int(
            response_json.get("dimensions") or response_json.get("embedding_dimensions") or 384
        )
        max_tokens = int(response_json.get("max_tokens") or self._infer_max_tokens(dimensions))
        batch_size = int(response_json.get("batch_size") or self._default_batch_size)

        self._cached_model_config = EmbeddingModelConfig(
            model_name=model_name,
            dimensions=dimensions,
            max_tokens=max_tokens,
            batch_size=batch_size,
        )
        self._cache_time = monotonic()
        self._current_batch_size = min(batch_size, self._default_batch_size)
        return self._cached_model_config

    async def batch_embed(self, texts: list[str]) -> dict[str, Any]:
        """Embed a batch of text strings with adaptive batch-size tuning."""
        if not texts:
            return {"embeddings": [], "model": None, "dimensions": 0}

        model_config = await self.fetch_embedding_model_config()
        effective_batch_size = min(self._current_batch_size, model_config.batch_size, len(texts))
        request_texts = texts[:effective_batch_size]

        start = monotonic()
        response_json = await self._request(
            "POST",
            "/embed/batch",
            json={"queries": request_texts, "model": None},
        )
        latency_seconds = monotonic() - start
        self._adjust_batch_size(latency_seconds)

        embeddings = response_json.get("embeddings")
        if not isinstance(embeddings, list):
            raise EmbeddingError("Embedding API did not return an embeddings list")

        return {
            "embeddings": embeddings,
            "model": response_json.get("model", model_config.model_name),
            "dimensions": int(response_json.get("dimensions", model_config.dimensions)),
            "batch_size_used": effective_batch_size,
            "latency_seconds": latency_seconds,
        }

    def _adjust_batch_size(self, latency_seconds: float) -> None:
        """Tune the next batch size based on observed latency."""
        if latency_seconds > 5 and self._current_batch_size > 25:
            self._current_batch_size = max(25, self._current_batch_size // 2)
        elif latency_seconds < 2 and self._current_batch_size < self._default_batch_size:
            self._current_batch_size = min(self._default_batch_size, self._current_batch_size + 25)

        logger.info(
            "Adjusted embedding batch size",
            latency_seconds=latency_seconds,
            batch_size=self._current_batch_size,
        )

    async def _request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send an HTTP request to the embedding service."""
        try:
            import httpx
        except ImportError as exc:
            raise EmbeddingError(
                "httpx is not installed. Install project dependencies"
                " before calling the embedding API."
            ) from exc

        headers: dict[str, str] = {}

        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(method, url, json=json, headers=headers)
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
        except Exception as exc:
            logger.exception("Embedding API request failed", method=method, url=url)
            raise EmbeddingError(f"Embedding API request failed: {exc}") from exc

    @staticmethod
    def _infer_max_tokens(dimensions: int) -> int:
        """Infer a conservative chunk budget when the API does not expose one."""
        if dimensions >= 1024:
            return 2048
        if dimensions >= 768:
            return 1536
        return 1024
