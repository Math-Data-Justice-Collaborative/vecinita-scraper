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


# Load .env file
_load_dotenv()


def _env(name: str, default: str = "") -> str:
    """Return environment value as a guaranteed string."""
    return os.getenv(name) or default


@dataclass
class SupabaseConfig:
    """Supabase configuration."""

    project_url: str
    publishable_key: str
    anon_key: str
    service_key: str

    @staticmethod
    def from_env() -> "SupabaseConfig":
        """Load Supabase config from environment."""
        return SupabaseConfig(
            project_url=_env("SUPABASE_URL") or _env("SUPABASE_PROJECT_URL"),
            publishable_key=_env("SUPABASE_PUBLISHABLE_KEY"),
            anon_key=_env("SUPABASE_ANON_KEY"),
            service_key=_env("SUPABASE_KEY") or _env("SUPABASE_SERVICE_KEY"),
        )

    def validate(self) -> None:
        """Validate all required fields are set."""
        if not all([self.project_url, self.publishable_key, self.anon_key]):
            raise ConfigError(
                "Missing required Supabase configuration: "
                "SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_ANON_KEY"
            )


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
    embedding_service_auth_token: str

    @staticmethod
    def from_env() -> "APIConfig":
        """Load API config from environment."""
        return APIConfig(
            vecinita_model_api_url=_env("VECINITA_MODEL_API_URL"),
            vecinita_embedding_api_url=_env("VECINITA_EMBEDDING_API_URL"),
            embedding_service_auth_token=_env("EMBEDDING_SERVICE_AUTH_TOKEN")
            or _env("VECINITA_EMBEDDING_API_TOKEN"),
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

        self.supabase = SupabaseConfig.from_env()
        self.modal = ModalConfig.from_env()
        self.api = APIConfig.from_env()
        self.crawl = CrawlConfig.from_env()
        self.chunking = ChunkingConfig.from_env()

    def validate(self) -> None:
        """Validate all configuration."""
        self.supabase.validate()
        if self.environment == "production":
            self.modal.validate()


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get cached configuration instance."""
    config = Config()
    config.validate()
    return config
