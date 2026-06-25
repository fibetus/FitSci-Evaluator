from src.config.settings import Settings, build_postgres_dsn, build_rabbitmq_url


def test_build_postgres_dsn_from_components(monkeypatch) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_USER", "app")
    monkeypatch.setenv("POSTGRES_PASSWORD", "s3cret")
    monkeypatch.setenv("POSTGRES_DB", "fitsci")

    assert build_postgres_dsn() == (
        "postgresql+asyncpg://app:s3cret@db.example.com:5433/fitsci"
    )


def test_build_rabbitmq_url_from_components(monkeypatch) -> None:
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    monkeypatch.setenv("RABBITMQ_HOST", "mq.example.com")
    monkeypatch.setenv("RABBITMQ_PORT", "5672")
    monkeypatch.setenv("RABBITMQ_USER", "app")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "s3cret")

    assert build_rabbitmq_url() == "amqp://app:s3cret@mq.example.com:5672/%2F"


def test_settings_local_defaults(monkeypatch) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    monkeypatch.setenv("FITSCI_DEPLOYMENT", "local")
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    settings = Settings.from_env()
    assert settings.deployment == "local"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert "localhost" in settings.postgres_dsn
