# backend-fastapi-high-performance-gateway

Built by [VisionQuantech](https://visionquantech.com) — AI agents, apps & tools for small businesses.

Real API gateway: FastAPI reverse proxy with a YAML routing table, per-route
token-bucket rate limiting, SQLite request logging, and live upstream health
checks.

## What it does

- **Reverse proxy** — longest-prefix route match from `routes.yaml`, optional
  prefix stripping, method/path/query/body forwarded via httpx.
- **Per-route rate limiting** — token bucket per route + client IP
  (e.g. `rate_limit: 20/minute`); exhausted buckets get **HTTP 429**.
- **Request logging** — every proxied request (method, path, route, upstream
  status, latency) logged to SQLite; view at `GET /admin/logs`.
- **Health checks** — `GET /admin/health` probes each upstream live (`/health`
  then `/`).
- Admin: `GET /health`, `GET /admin/routes`, `GET /admin/logs`.

## Configuration

`routes.yaml`:
```yaml
routes:
  - name: users-api
    path_prefix: /api/users
    target: http://127.0.0.1:9001
    strip_prefix: true
    rate_limit: 100/minute
```

| Env var          | Purpose                        | Default            |
|------------------|--------------------------------|--------------------|
| `GATEWAY_ROUTES` | routing table path             | `./routes.yaml`    |
| `GATEWAY_DB`     | request-log SQLite path        | `./gateway_logs.db`|

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --port 8006
```

## Tests

```bash
python -m pytest tests/ -q
```

Tests spin up a real upstream echo service and verify: prefix stripping +
query/body forwarding, 429 after the 3/minute budget is spent, SQLite logs
contain the requests (including the 429s), live health checks report the
upstream as `up`, unmatched paths 404.