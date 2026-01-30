"""Strands Agent OpenTelemetry tracing setup.

Initializes StrandsTelemetry with an OTLP exporter so that all Strands Agent
invocations (which already carry ``trace_attributes``) are exported to the
configured backend (e.g. Opik / Comet).

The underlying ``OTLPSpanExporter`` reads endpoint and header configuration
directly from the standard environment variables:

- ``OTEL_EXPORTER_OTLP_ENDPOINT``
- ``OTEL_EXPORTER_OTLP_HEADERS``

so no manual parsing is needed here.
"""

from strands.telemetry import StrandsTelemetry

from core.config import settings

_telemetry: StrandsTelemetry | None = None


def setup_tracing() -> None:
    """Configure Strands OTLP tracing if enabled via settings.

    Relies on ``OTEL_EXPORTER_OTLP_ENDPOINT`` and
    ``OTEL_EXPORTER_OTLP_HEADERS`` being set in the environment.

    Safe to call multiple times; only the first invocation takes effect.
    """
    global _telemetry

    if _telemetry is not None:
        return

    if not settings.opik_tracing_enabled:
        return

    _telemetry = StrandsTelemetry()
    _telemetry.setup_otlp_exporter()
