"""Configuration settings for Fiscal Guard."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fiscal_guard"

    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # Strands AI Configuration
    strands_default_model: str = "gemini-3-flash-preview"

    # Google AI (for Gemini)
    google_api_key: str = ""

    # Opik (via OpenTelemetry)
    # Note: OTEL_EXPORTER_OTLP_ENDPOINT and OTEL_EXPORTER_OTLP_HEADERS
    # are handled directly by OpenTelemetry and don't need to be in this config
    opik_tracing_enabled: bool = False


settings = Settings()
