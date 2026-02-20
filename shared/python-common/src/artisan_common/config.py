"""Centralized configuration management using Pydantic Settings.

Every service inherits from BaseServiceSettings and extends it
with service-specific fields. Configuration is loaded from:
  1. Environment variables (highest priority — used in K8s via ConfigMaps/Secrets)
  2. .env file (local development)
  3. Field defaults (sensible fallbacks)

Usage in a service:
    from artisan_common.config import BaseServiceSettings

    class GallerySettings(BaseServiceSettings):
        s3_bucket: str = "artisan-gallery"
        max_upload_size_mb: int = 10

    settings = GallerySettings()
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base configuration shared by all Artisan services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Service Identity ──────────────────────────────────────
    service_name: str = "artisan-service"
    service_version: str = "0.1.0"
    environment: str = "local"  # local | dev | staging | prod
    debug: bool = False
    log_level: str = "INFO"

    # ── Server ────────────────────────────────────────────────
    host: str = "0.0.0.0"  # noqa: S104 — bind all interfaces (required in Docker/K8s)
    port: int = 8000

    # ── Database (PostgreSQL) ─────────────────────────────────
    database_url: str = "postgresql+asyncpg://artisan:artisan@localhost:5432/artisan"

    # ── Cache (Redis) ─────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Messaging (NATS) ──────────────────────────────────────
    nats_url: str = "nats://localhost:4222"

    # ── Auth (Keycloak) ───────────────────────────────────────
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "artisan"
    jwt_audience: str = "artisan-api"

    # ── Observability (OpenTelemetry) ─────────────────────────
    otel_exporter_endpoint: str = "http://localhost:4317"
    otel_enabled: bool = True
