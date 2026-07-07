import time
import random
import logging
from flask import Flask, jsonify, request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
    REGISTRY,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── Prometheus Metrics ─────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP error count",
    ["method", "endpoint", "status_code"],
)

IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)


# ── Middleware: track every request ───────────────────────────────────────────
@app.before_request
def before_request():
    request.start_time = time.time()
    IN_PROGRESS.inc()


@app.after_request
def after_request(response):
    latency = time.time() - request.start_time
    endpoint = request.path
    method = request.method
    status = str(response.status_code)

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

    if response.status_code >= 400:
        ERROR_COUNT.labels(method=method, endpoint=endpoint, status_code=status).inc()

    IN_PROGRESS.dec()

    logger.info(
        "%s %s → %s (%.4fs)", method, endpoint, status, latency
    )
    return response


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Liveness probe — always returns 200."""
    return jsonify({"status": "ok", "service": "docker-cicd-monitoring"}), 200


@app.route("/items", methods=["GET"])
def list_items():
    """Returns a static list of items with a simulated small latency."""
    time.sleep(random.uniform(0.005, 0.05))
    items = [
        {"id": 1, "name": "Widget Alpha"},
        {"id": 2, "name": "Widget Beta"},
        {"id": 3, "name": "Widget Gamma"},
    ]
    return jsonify({"items": items, "count": len(items)}), 200


@app.route("/chaos", methods=["GET"])
def chaos():
    """Randomly returns a 500 error ~20% of the time to simulate failures."""
    if random.random() < 0.2:
        return jsonify({"error": "Internal chaos error — try again"}), 500
    time.sleep(random.uniform(0.01, 0.3))
    return jsonify({"message": "Chaos endpoint — you survived!"}), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus scrape endpoint."""
    return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
