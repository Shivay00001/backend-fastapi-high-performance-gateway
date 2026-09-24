"""backend-fastapi-high-performance-gateway: real API gateway.

- Reverse proxy with a YAML routing table (routes.yaml): longest-prefix match,
  optional prefix stripping, per-route upstreams.
- Per-route token-bucket rate limiting (per client IP); 429 when exhausted.
- Every proxied request logged to SQLite (method, path, route, status, latency).
- Live upstream health checks at GET /admin/health.
- Gateway admin: GET /health, GET /admin/routes, GET /admin/logs.
"""
import os
import time

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

import logstore
from logstore import init_db, log_request, recent_logs
from ratelimit import RateLimiter
from routes import load_routes

logstore.init_db()

app = FastAPI(title="API Gateway", version="1.0.0")
limiter = RateLimiter()
ROUTES = load_routes()

HOP_HEADERS = {"host", "content-length", "connection", "transfer-encoding",
               "keep-alive", "proxy-authenticate", "proxy-authorization",
               "te", "trailer", "upgrade"}


def match_route(path: str):
    for r in ROUTES:
        if path == r["path_prefix"] or path.startswith(r["path_prefix"].rstrip("/") + "/"):
            return r
    return None


def check_upstream(route: dict, timeout: float = 5.0) -> dict:
    """Real live health probe against the upstream."""
    for probe in ("/health", "/"):
        try:
            resp = httpx.get(route["target"] + probe, timeout=timeout)
            if resp.status_code < 500:
                return {"name": route["name"], "target": route["target"],
                        "probe": probe, "status": "up",
                        "http_status": resp.status_code}
        except httpx.HTTPError:
            continue
    return {"name": route["name"], "target": route["target"],
            "status": "down", "http_status": None}


@app.get("/health")
def health():
    return {"status": "ok", "routes": len(ROUTES)}


@app.get("/admin/routes")
def admin_routes():
    return {"routes": [
        {k: r[k] for k in ("name", "path_prefix", "target", "rate_limit", "strip_prefix")}
        for r in ROUTES]}


@app.get("/admin/health")
def admin_health():
    return {"upstreams": [check_upstream(r) for r in ROUTES]}


@app.get("/admin/logs")
def admin_logs(limit: int = 100):
    return {"logs": recent_logs(min(limit, 500))}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy(path: str, request: Request):
    full_path = "/" + path
    route = match_route(full_path)
    client_ip = request.client.host if request.client else "unknown"
    t0 = time.monotonic()

    if route is None:
        return JSONResponse({"error": f"no route matches {full_path}"}, status_code=404)

    if not limiter.allow(route["name"], client_ip, route["capacity"], route["refill_per_sec"]):
        log_request(client_ip, request.method, full_path, route["name"], 429,
                    (time.monotonic() - t0) * 1000)
        return JSONResponse({"error": "rate limit exceeded",
                             "route": route["name"],
                             "limit": route["rate_limit"]}, status_code=429)

    upstream_path = full_path
    if route["strip_prefix"]:
        upstream_path = full_path[len(route["path_prefix"]):] or "/"
    url = route["target"] + upstream_path
    if request.url.query:
        url += "?" + request.url.query

    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_HEADERS}
    body = await request.body()

    try:
        resp = httpx.request(request.method, url, headers=headers,
                             content=body, timeout=30.0)
    except httpx.HTTPError as e:
        log_request(client_ip, request.method, full_path, route["name"], 502,
                    (time.monotonic() - t0) * 1000)
        return JSONResponse({"error": "upstream unreachable", "detail": str(e)[:200]},
                            status_code=502)

    log_request(client_ip, request.method, full_path, route["name"], resp.status_code,
                (time.monotonic() - t0) * 1000)
    out_headers = {k: v for k, v in resp.headers.items() if k.lower() not in HOP_HEADERS}
    return Response(content=resp.content, status_code=resp.status_code,
                    headers=out_headers,
                    media_type=resp.headers.get("content-type"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8006)))
