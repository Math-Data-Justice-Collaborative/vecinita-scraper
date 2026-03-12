"""Modal App initialization with queues and shared infrastructure."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

modal: Any
try:
    import modal as _modal

    modal = _modal
except ImportError:  # pragma: no cover - used only in local test environments without Modal
    class _DummyAsyncMethod:
        async def aio(self, *args: Any, **kwargs: Any) -> Any:
            return None

    class _DummyQueue:
        def __init__(self) -> None:
            self.put = _DummyAsyncMethod()
            self.get = _DummyAsyncMethod()

        @classmethod
        def from_name(cls, name: str, create_if_missing: bool = False) -> _DummyQueue:
            return cls()

    class _DummyImage:
        @staticmethod
        def debian_slim() -> _DummyImage:
            return _DummyImage()

        def pip_install(self, *packages: str) -> _DummyImage:
            return self

        def add_local_python_source(self, *packages: str) -> _DummyImage:
            return self

    class _DummySecret:
        @staticmethod
        def from_name(name: str) -> str:
            return name

    class _DummyFunctionWrapper:
        def __init__(self, func: Callable[..., Any]) -> None:
            self._func = func
            self.spawn = _DummyAsyncMethod()

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return self._func(*args, **kwargs)

    class _DummyApp:
        def __init__(self, name: str) -> None:
            self.name = name
            self.image = None

        def function(self, **kwargs: Any) -> Callable[[Callable[..., Any]], _DummyFunctionWrapper]:
            def decorator(func: Callable[..., Any]) -> _DummyFunctionWrapper:
                return _DummyFunctionWrapper(func)

            return decorator

    class _DummyModalModule:
        App = _DummyApp
        Image = _DummyImage
        Queue = _DummyQueue
        Secret = _DummySecret

        @staticmethod
        def batched(**kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                return func

            return decorator

    modal = _DummyModalModule()

# Create Modal app
app = modal.App(name="vecinita-scraper")
APP_SECRETS = [modal.Secret.from_name("vecinita-scraper-env")]

# Define image with dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "crawl4ai>=0.4.0",
        "docling>=0.4.0",
        "langchain>=0.1.0",
        "tiktoken>=0.5.0",
        "fastapi>=0.100",
        "uvicorn>=0.23.0",
        "httpx>=0.25.0",
        "supabase>=2.0.0",
        "pydantic>=2.0",
        "python-dotenv>=1.0",
        "structlog>=23.0",
        "aiohttp>=3.8.0",
    )
    .add_local_python_source("vecinita_scraper")
)

# Create app with custom image
app.image = image

# Initialize queues for worker communication
# These queues are the backbone of the job processing pipeline

# Queue for initial scraping job submissions
scrape_jobs_queue = modal.Queue.from_name(
    "scrape-jobs",
    create_if_missing=True,
)

# Queue for document processing tasks
process_jobs_queue = modal.Queue.from_name(
    "process-jobs",
    create_if_missing=True,
)

# Queue for chunking tasks
chunk_jobs_queue = modal.Queue.from_name(
    "chunk-jobs",
    create_if_missing=True,
)

# Queue for embedding tasks
embed_jobs_queue = modal.Queue.from_name(
    "embed-jobs",
    create_if_missing=True,
)

# Queue for storage/finalization tasks
store_jobs_queue = modal.Queue.from_name(
    "store-jobs",
    create_if_missing=True,
)


@app.function(secrets=APP_SECRETS)
def health_check() -> dict[str, str]:
    """Health check endpoint for Modal workers."""
    return {"status": "ok", "worker": "vecinita-scraper"}


# Import worker modules after the shared app and queues are defined so Modal
# registers decorated functions during deployment.
from vecinita_scraper.workers import chunker as _chunker  # noqa: E402,F401
from vecinita_scraper.workers import embedder as _embedder  # noqa: E402,F401
from vecinita_scraper.workers import finalizer as _finalizer  # noqa: E402,F401
from vecinita_scraper.workers import processor as _processor  # noqa: E402,F401
from vecinita_scraper.workers import scraper as _scraper  # noqa: E402,F401

# Note: FastAPI app is served separately via Modal's web endpoint deployment.
# See src/vecinita_scraper/api/server.py for the REST API implementation.


if __name__ == "__main__":
    # Local entrypoint for testing
    result = health_check.remote()
    print(result)
