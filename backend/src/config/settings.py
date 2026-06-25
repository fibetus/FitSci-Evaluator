"""Environment-backed settings for local dev and VPS deployment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote_plus

from dotenv import load_dotenv

from ..domain.errors import ConfigurationError

load_dotenv()


def _require(value: str | None, name: str) -> str:
    if not value:
        raise ConfigurationError(f"Missing required configuration: {name}")
    return value


def build_postgres_dsn(
    *,
    host: str | None = None,
    port: str | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
    driver: str = "postgresql+asyncpg",
) -> str:
    """Build an async SQLAlchemy DSN from components or POSTGRES_DSN."""
    explicit = os.getenv("POSTGRES_DSN")
    if explicit:
        return explicit

    resolved_host = host or os.getenv("POSTGRES_HOST", "localhost")
    resolved_port = port or os.getenv("POSTGRES_PORT", "5432")
    resolved_user = user or os.getenv("POSTGRES_USER", "fitsci") or "fitsci"
    resolved_password = (
        password if password is not None else os.getenv("POSTGRES_PASSWORD", "fitsci")
    ) or "fitsci"
    resolved_db = database or os.getenv("POSTGRES_DB", "fitsci")

    safe_user = quote_plus(resolved_user)
    safe_password = quote_plus(resolved_password)
    return (
        f"{driver}://{safe_user}:{safe_password}"
        f"@{resolved_host}:{resolved_port}/{resolved_db}"
    )


def build_postgres_sync_dsn(async_dsn: str | None = None) -> str:
    """Alembic uses a synchronous driver."""
    dsn = async_dsn or build_postgres_dsn()
    return dsn.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)


def build_rabbitmq_url(
    *,
    host: str | None = None,
    port: str | None = None,
    user: str | None = None,
    password: str | None = None,
    vhost: str | None = None,
) -> str:
    explicit = os.getenv("RABBITMQ_URL")
    if explicit:
        return explicit

    resolved_host = host or os.getenv("RABBITMQ_HOST", "localhost")
    resolved_port = port or os.getenv("RABBITMQ_PORT", "5672")
    resolved_user = user or os.getenv("RABBITMQ_USER", "fitsci") or "fitsci"
    resolved_password = (
        password if password is not None else os.getenv("RABBITMQ_PASSWORD", "fitsci")
    ) or "fitsci"
    resolved_vhost = vhost or os.getenv("RABBITMQ_VHOST", "/") or "/"
    safe_vhost = quote_plus(resolved_vhost)

    safe_user = quote_plus(resolved_user)
    safe_password = quote_plus(resolved_password)
    return (
        f"amqp://{safe_user}:{safe_password}@{resolved_host}:{resolved_port}/{safe_vhost}"
    )


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration loaded from the environment."""

    deployment: str
    postgres_dsn: str
    postgres_sync_dsn: str
    rabbitmq_url: str
    ollama_base_url: str
    gemma_model_tag: str
    log_level: str
    rate_limit_per_minute: int
    ncbi_api_key: str | None

    @classmethod
    def from_env(cls) -> Settings:
        deployment = os.getenv("FITSCI_DEPLOYMENT", "local").lower()
        if deployment not in {"local", "vps"}:
            raise ConfigurationError(
                "FITSCI_DEPLOYMENT must be 'local' or 'vps' (got "
                f"{deployment!r})"
            )

        postgres_dsn = build_postgres_dsn()
        return cls(
            deployment=deployment,
            postgres_dsn=postgres_dsn,
            postgres_sync_dsn=build_postgres_sync_dsn(postgres_dsn),
            rabbitmq_url=build_rabbitmq_url(),
            ollama_base_url=_require(
                os.getenv("OLLAMA_BASE_URL"), "OLLAMA_BASE_URL"
            )
            if deployment == "vps"
            else (os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"),
            gemma_model_tag=os.getenv("GEMMA_MODEL_TAG", "gemma4:12b-q4_k_m"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")),
            ncbi_api_key=os.getenv("NCBI_API_KEY") or None,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
