"""Configuration loading from environment variables."""

import os
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from vecinita_scraper.core.errors import ConfigError

_dotenv_load: Callable[..., bool] | None
try:
    from dotenv import load_dotenv as _dotenv_load
except ImportError:  # pragma: no cover - fallback for minimal test environments
    _dotenv_load = None


def _load_dotenv() -> bool:
    if _dotenv_load is None:
        return False
    dotenv_loader: Callable[..., bool] = _dotenv_load
    return dotenv_loader()


_load_dotenv()


def _env(name: str, default: str = "") -> str:
    """Return environment value as a guaranteed string."""
    return os.getenv(name) or default


@dataclass
class PostgresConfig:
    """Render Postgres configuration."""

    database_url: str

    @staticmethod
    def from_env() -> "PostgresConfig":
        """Load Postgres config from environment."""
        return PostgresConfig(database_url=_env("DATABASE_URL"))

    def validate(self) -> None:
        """Validate Postgres configuration."""
        if not self.database_url:
            raise ConfigError("Missing required Postgres configuration: DATABASE_URL")


@dataclass
class ModalConfig:
    """Modal configuration."""

    token_id: str
    token_secret: str
    workspace: str

    @staticmethod
    def from_env() -> "ModalConfig":
        """Load Modal config from environment."""
        return ModalConfig(
            token_id=os.getenv("MODAL_TOKEN_ID", ""),
            token_secret=os.getenv("MODAL_TOKEN_SECRET", ""),
            workspace=os.getenv("MODAL_WORKSPACE", ""),
        )

    def validate(self) -> None:
        """Validate Modal config (optional in dev, required in prod)."""
        if os.getenv("ENVIRONMENT") == "production":
            if not all([self.token_id, self.token_secret]):
                raise ConfigError(
                    "Missing required Modal configuration in production: "
                    "MODAL_TOKEN_ID, MODAL_TOKEN_SECRET"
                )


@dataclass
class APIConfig:
    """External API configuration."""

    vecinita_model_api_url: str
    vecinita_embedding_api_url: str

    @staticmethod
    def from_env() -> "APIConfig":
        """Load API config from environment."""
        return APIConfig(
            vecinita_model_api_url=_env("VECINITA_MODEL_API_URL"),
            vecinita_embedding_api_url=_env("VECINITA_EMBEDDING_API_URL"),
        )

    def validate(self) -> None:
        """Validate API config."""
        if not all(
            [
                self.vecinita_embedding_api_url,
            ]
        ):
            raise ConfigError("Missing required API configuration: VECINITA_EMBEDDING_API_URL")


@dataclass
class CrawlConfig:
    """Crawl4AI configuration."""

    timeout_seconds: int
    max_depth: int

    @staticmethod
    def from_env() -> "CrawlConfig":
        """Load crawl config from environment."""
        return CrawlConfig(
            timeout_seconds=int(os.getenv("CRAWL4AI_TIMEOUT_SECONDS", "60")),
            max_depth=int(os.getenv("CRAWL4AI_MAX_DEPTH", "3")),
        )


@dataclass
class ChunkingConfig:
    """Chunking configuration."""

    min_size_tokens: int
    max_size_tokens: int
    overlap_ratio: float

    @staticmethod
    def from_env() -> "ChunkingConfig":
        """Load chunking config from environment."""
        return ChunkingConfig(
            min_size_tokens=int(os.getenv("CHUNK_MIN_SIZE_TOKENS", "256")),
            max_size_tokens=int(os.getenv("CHUNK_MAX_SIZE_TOKENS", "1024")),
            overlap_ratio=float(os.getenv("CHUNK_OVERLAP_RATIO", "0.2")),
        )


class Config:
    """Main configuration class."""

    def __init__(self) -> None:
        """Initialize configuration from environment."""
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        self.postgres = PostgresConfig.from_env()
        self.modal = ModalConfig.from_env()
        self.api = APIConfig.from_env()
        self.crawl = CrawlConfig.from_env()
        self.chunking = ChunkingConfig.from_env()

    def validate(self) -> None:
        """Validate all configuration."""
        self.postgres.validate()
        if self.environment == "production":
            self.modal.validate()


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get cached configuration instance."""
    config = Config()
    config.validate()
    return config
