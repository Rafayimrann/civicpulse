"""
Prometheus metric objects, defined once at import time (the prometheus_client
convention) and used by middleware.py and services/triage_service.py.
"""
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "civicpulse_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "civicpulse_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

TRIAGE_LATENCY = Histogram(
    "civicpulse_triage_duration_seconds",
    "Triage classification latency in seconds",
    ["provider"],
)

TRIAGE_FALLBACK_COUNT = Counter(
    "civicpulse_triage_fallback_total",
    "Number of times triage fell back to RuleBasedTriage",
)
