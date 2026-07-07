# RUNBOOK — docker-cicd-monitoring

> **Version:** 1.0 | **Last updated:** 2026-07-07  
> **Maintainer:** Your Name / Team  
> **Escalation:** #oncall Slack channel | PagerDuty policy: `flask-api`

---

## Overview

This runbook covers operational procedures for the **docker-cicd-monitoring** stack:

| Service       | Port  | Description                        |
|---------------|-------|------------------------------------|
| Flask API     | 5000  | REST API (3 endpoints + /metrics)  |
| Prometheus    | 9090  | Metrics collection & alerting      |
| Grafana       | 3000  | Dashboards & visualization         |

---

## Alert: Error Rate > 5%

### Symptom
Grafana **"Error Rate (%)"** gauge is red (≥ 5%) or you receive a Prometheus alert for  
`http_errors_total rate`.

### 1 — Identify the failing endpoint

```promql
# Which endpoints are erroring most?
sum(rate(http_errors_total[5m])) by (endpoint, status_code)
```

Open [Prometheus UI → Graph](http://localhost:9090) and run this query.

### 2 — Check application logs

```bash
# Docker Compose
docker compose logs --tail=200 api

# Or follow live
docker compose logs -f api
```

Look for Python tracebacks, connection errors, or 5xx log lines.

### 3 — Check if the issue is /chaos (expected noise)

The `/chaos` endpoint intentionally returns 500 ~20% of the time.  
If all errors are from `/chaos`, **this is not a real incident** — verify other endpoints are healthy.

```bash
curl -s http://localhost:5000/health
curl -s http://localhost:5000/items
```

### 4 — Restart the API container

If the API is crashing or stuck:

```bash
docker compose restart api
```

Wait 15 seconds and re-check the Grafana error rate gauge.

### 5 — Full stack restart

If restarting the API alone doesn't help:

```bash
docker compose down
docker compose up -d
```

### 6 — Escalate

If error rate remains > 5% after restart:
- Post in **#oncall** with the Grafana screenshot and relevant log lines.
- Page the on-call engineer via PagerDuty if SLA window is breached.

---

## Alert: P95 Latency > 1 second

### Symptom
Grafana **"P95 Latency"** stat panel is red or the `http_request_duration_seconds` histogram shows high values.

### 1 — Identify slow endpoints

```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)
```

### 2 — Check container resource usage

```bash
docker stats cicd_api cicd_prometheus cicd_grafana
```

If CPU/memory are pegged, the host may be under-resourced.

### 3 — Scale workers

Edit `app/Dockerfile` CMD section and increase `--workers`:

```dockerfile
CMD ["gunicorn", "--workers", "4", "--threads", "4", ...]
```

Then rebuild:

```bash
docker compose build api
docker compose up -d api
```

### 4 — Restart

```bash
docker compose restart api
```

---

## Alert: API is Unreachable (health check failing)

### Symptom
`curl http://localhost:5000/health` returns no response or connection refused.

### Steps

```bash
# 1. Check if the container is running
docker compose ps

# 2. Check recent logs
docker compose logs --tail=100 api

# 3. Restart the container
docker compose restart api

# 4. If the container keeps exiting, rebuild
docker compose build --no-cache api
docker compose up -d api
```

---

## Alert: Prometheus Not Scraping

### Symptom
Grafana shows "No data" or metrics are stale.

### Steps

```bash
# 1. Open Prometheus targets page
# http://localhost:9090/targets
# The flask_api target should be UP

# 2. Check Prometheus container logs
docker compose logs prometheus

# 3. Validate config
docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# 4. Reload config without restart
curl -X POST http://localhost:9090/-/reload

# 5. Restart if needed
docker compose restart prometheus
```

---

## Grafana — Reset Admin Password

```bash
docker compose exec grafana grafana-cli admin reset-admin-password newpassword
```

---

## Quick Reference Commands

| Action                        | Command                                      |
|-------------------------------|----------------------------------------------|
| Start all services            | `docker compose up -d`                       |
| Stop all services             | `docker compose down`                        |
| Restart single service        | `docker compose restart <service>`           |
| View logs                     | `docker compose logs -f <service>`           |
| Check container health        | `docker compose ps`                          |
| Rebuild image                 | `docker compose build --no-cache api`        |
| Manual metrics scrape check   | `curl http://localhost:5000/metrics`         |
| Prometheus expression browser | `http://localhost:9090`                      |
| Grafana dashboard             | `http://localhost:3000` (admin/admin)        |
