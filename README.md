# docker-cicd-monitoring

A production-style **Flask API** fully instrumented with **Prometheus** metrics, orchestrated with **Docker Compose**, visualized in **Grafana**, and shipped via a **GitHub Actions** CI/CD pipeline.

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                       │
│                                                         │
│  ┌──────────────┐  /metrics   ┌──────────────────────┐  │
│  │  Flask API   │ ──────────▶ │     Prometheus       │  │
│  │  :5000       │             │     :9090            │  │
│  └──────────────┘             └──────────────────────┘  │
│                                         │               │
│                                         │ datasource    │
│                                         ▼               │
│                               ┌──────────────────────┐  │
│                               │       Grafana        │  │
│                               │       :3000          │  │
│                               └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```
## 🚀 Quick Start
### 1. Clone the repository

```bash
git clone https://github.com/ansari6926/docker-cicd-monitoring.git
cd docker-cicd-monitoring
```

### 2. Start all services

```bash
docker compose up -d --build
```

This will:
- Build the Flask API image from `app/Dockerfile`
- Start **Prometheus** (scraping `/metrics` every 10s)
- Start **Grafana** (pre-configured with Prometheus datasource + dashboard)

### 3. Verify everything is running

```bash
docker compose ps
```

All three services should show `healthy` or `running`.

---

## 🔌 API Endpoints

| Method | Endpoint   | Description                                      |
|--------|------------|--------------------------------------------------|
| GET    | `/health`  | Liveness probe — always returns `200 OK`         |
| GET    | `/items`   | Returns a list of 3 widgets (simulated latency)  |
| GET    | `/chaos`   | Returns 500 ~20% of the time (chaos simulation)  |
| GET    | `/metrics` | Prometheus scrape endpoint                       |

---

## 📊 Grafana Dashboard

The dashboard **"Flask API — CI/CD Monitoring"** is auto-provisioned and includes:

| Panel                          | PromQL                                                                                               |
|--------------------------------|------------------------------------------------------------------------------------------------------|
| 🚀 Requests/sec                | `sum(rate(http_requests_total[1m]))`                                                                 |
| 🔴 Error Rate (%)              | `100 * sum(rate(http_errors_total[1m])) / (sum(rate(http_requests_total[1m])) + 0.0001)`            |
| ⏱️ P95 Latency                 | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`             |
| 🔄 Requests In Progress        | `http_requests_in_progress`                                                                          |
| Req/s by Endpoint (timeseries) | `sum(rate(http_requests_total[1m])) by (endpoint)`                                                   |
| Latency P50/P95/P99            | `histogram_quantile(0.9x, ...)`                                                                      |
| Errors by Endpoint             | `sum(rate(http_errors_total[1m])) by (endpoint, status_code)`                                        |

---

## 🔁 CI/CD Pipeline (GitHub Actions)

File: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

### Triggers
- Every `git push` to any branch
- Pull requests targeting `main`

### Jobs

| Job              | What it does                                                         |
|------------------|----------------------------------------------------------------------|
| `build-and-test` | Builds the Docker image, starts the container, runs 3 smoke tests   |
| `push`           | Logs into Docker Hub and pushes the image (only on `main` branch)   |

### Smoke tests
1. **`/health`** — must return HTTP 200
2. **`/items`** — must return HTTP 200
3. **`/metrics`** — response body must contain `http_requests_total`

---

## 🗂️ Project Structure

```
docker-cicd-monitoring/
├── app/
│   ├── app.py              # Flask API + Prometheus instrumentation
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Multi-stage Docker build
├── prometheus/
│   └── prometheus.yml      # Scrape config
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasource.yml   # Prometheus datasource
│   │   └── dashboards/
│   │       └── dashboard.yml    # Dashboard provider config
│   └── dashboards/
│       └── api_dashboard.json   # Pre-built dashboard
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI/CD
├── docker-compose.yml
├── RUNBOOK.md              # Operational runbook
└── README.md
```

---

## 🛑 Stopping the Stack

```bash
# Stop containers (keep volumes)
docker compose stop

# Stop and remove containers + networks
docker compose down

# Stop and remove everything including volumes
docker compose down -v
```

---

## 📋 Operational Runbook

See [RUNBOOK.md](RUNBOOK.md) for incident response procedures including:
- Error rate > 5% → check logs → restart API
- P95 latency spike → scale workers → restart
- API unreachable → rebuild image
- Prometheus not scraping → reload config

---

## 📝 License

MIT — see [LICENSE](LICENSE) for details.
