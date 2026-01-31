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
    strands_default_model: str = "gemini-2.5-flash"
    strands_vision_model: str = "gemini-2.0-flash-exp"

    # Google AI (for Gemini)
    google_api_key: str = ""

    # OpenTelemetry / Opik tracing
    # OTEL_EXPORTER_OTLP_ENDPOINT and OTEL_EXPORTER_OTLP_HEADERS are read
    # directly by the OTLPSpanExporter from the environment.
    opik_tracing_enabled: bool = False

    # Internal API for testing/evaluation
    allow_internal_endpoints: bool = False
    internal_api_token: str = ""


settings = Settings()
