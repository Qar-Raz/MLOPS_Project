from time import perf_counter
from typing import Callable, Awaitable
from fastapi import Request
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# -------------
# Core metrics
# -------------

# Total number of inference requests (your /predict calls).
# Using *_total is Prometheus best practice for Counters. They only ever go up. :contentReference[oaicite:1]{index=1}
REQUEST_COUNT = Counter(
    "smarttagger_requests_total",
    "Total number of /predict requests received.",
)

# Histogram of request latency in seconds.
# Histograms are the recommended way to get p95/p99 latency via histogram_quantile()
# in Prometheus/Grafana dashboards. This is a common FastAPI monitoring pattern. :contentReference[oaicite:2]{index=2}
REQUEST_LATENCY = Histogram(
    "smarttagger_request_latency_seconds",
    "Time spent handling /predict requests.",
)

# Gauge for in-flight requests right now.
# Gauges go up and down and are used in modern observability setups
# to see concurrency / load. :contentReference[oaicite:3]{index=3}
IN_PROGRESS = Gauge(
    "smarttagger_inprogress_requests",
    "Number of /predict requests currently being processed.",
)

# Custom business metric: total tokens processed.
# This is specific to your ML use case, and tracking this in Grafana is exactly
# what MLOps teams do to correlate usage volume with latency or errors. :contentReference[oaicite:4]{index=4}
TOKENS_TOTAL = Counter(
    "smarttagger_tokens_total",
    "Total tokens processed by /predict.",
)

# -------------
# Helper functions
# -------------


def export_metrics():
    """
    Returns (body_bytes, content_type) for the /metrics endpoint.
    Prometheus scrapes this on a fixed interval.
    This matches the standard FastAPI + Prometheus approach where you expose
    generate_latest() at /metrics so Prometheus can scrape it. :contentReference[oaicite:5]{index=5}
    """
    body = generate_latest()
    return body, CONTENT_TYPE_LATEST
