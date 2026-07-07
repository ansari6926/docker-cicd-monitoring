# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="docker-cicd-monitoring"
LABEL org.opencontainers.image.description="Flask API with Prometheus metrics"

# Prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Dependencies ──────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY app.py .

# Expose the application port
EXPOSE 5000

# ── Run with Gunicorn ─────────────────────────────────────────────────────────
# 2 workers, 4 threads each — appropriate for a small API container
CMD ["gunicorn", "--workers", "2", "--threads", "4", \
     "--bind", "0.0.0.0:5000", "--access-logfile", "-", "app:app"]
