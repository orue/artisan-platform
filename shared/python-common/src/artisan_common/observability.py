"""OpenTelemetry and structured logging setup.

Call setup_observability() once at service startup to configure:
  - Structured JSON logging via structlog
  - OpenTelemetry tracing with OTLP export
  - Trace ID injection into log entries

This gives you correlated logs and traces across services in Grafana.

Usage:
    from artisan_common.observability import setup_observability

    setup_observability(service_name="gallery-service", service_version="0.1.0")
"""

import logging
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def setup_observability(
    service_name: str,
    service_version: str,
    otel_endpoint: str | None = None,
    log_level: str = "INFO",
    otel_enabled: bool = True,
) -> None:
    """Initialize OpenTelemetry tracing and structured logging.

    Args:
        service_name: Name of the calling service (e.g., "gallery-service").
        service_version: Semantic version of the service.
        otel_endpoint: OTLP collector endpoint. None uses console exporter.
        log_level: Python log level string.
        otel_enabled: Set False to disable tracing (e.g., in tests).
    """
    _setup_logging(service_name, log_level)

    if otel_enabled:
        _setup_tracing(service_name, service_version, otel_endpoint)


def _setup_logging(service_name: str, log_level: str) -> None:
    """Configure structlog for JSON-formatted output with trace correlation."""

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_trace_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelNamesMapping()[log_level.upper()]),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _add_trace_context(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Inject OpenTelemetry trace and span IDs into every log entry."""
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = f"{ctx.trace_id:032x}"
        event_dict["span_id"] = f"{ctx.span_id:016x}"
    return event_dict


def _setup_tracing(
    service_name: str,
    service_version: str,
    otel_endpoint: str | None,
) -> None:
    """Configure OpenTelemetry with OTLP exporter or console fallback."""
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    provider = TracerProvider(resource=resource)

    if otel_endpoint:
        # OTLP gRPC exporter — used in Docker/K8s environments
        # Lazy import: only needed when sending to a real collector
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
    else:
        # Console exporter — used in local development
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
