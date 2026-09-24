import json
import os
import threading
import time

# sandbox quirk: stock NO_PROXY contains patterns httpx cannot parse
# (*[::1]); use a minimal one so localhost bypasses the egress proxy.
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# test upstream: tiny echo service on :18061
upstream = FastAPI()


@upstream.api_route("/echo/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def echo(path: str, request: Request):
    body = (await request.body()).decode()
    return JSONResponse({"upstream": True, "method": request.method,
                         "path": "/" + path, "query": dict(request.query_params),
                         "body": body})


@upstream.get("/health")
def uhealth():
    return {"status": "ok"}


def _serve():
    uvicorn.run(upstream, host="127.0.0.1", port=18061, log_level="error")


t = threading.Thread(target=_serve, daemon=True)
t.start()
time.sleep(1.5)

ROUTES_YAML = """
routes:
  - name: echo-api
    path_prefix: /api
    target: http://127.0.0.1:18061
    strip_prefix: true
    rate_limit: 100/minute
  - name: tight
    path_prefix: /tight
    target: http://127.0.0.1:18061
    strip_prefix: true
    rate_limit: 3/minute
"""
with open("/tmp/gw-routes.yaml", "w") as f:
    f.write(ROUTES_YAML)
os.environ["GATEWAY_ROUTES"] = "/tmp/gw-routes.yaml"
os.environ["GATEWAY_DB"] = "/tmp/gw-test.db"
if os.path.exists("/tmp/gw-test.db"):
    os.remove("/tmp/gw-test.db")

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def test_proxy_get_strips_prefix_and_forwards_query():
    r = client.get("/api/echo/things/42?x=1&y=2")
    assert r.status_code == 200
    body = r.json()
    assert body["upstream"] is True
    assert body["path"] == "/things/42"  # /api stripped by gateway
    assert body["query"] == {"x": "1", "y": "2"}


def test_proxy_post_forwards_body():
    r = client.post("/api/echo/submit", json={"a": 1})
    assert r.status_code == 200
    assert json.loads(r.json()["body"]) == {"a": 1}
    assert r.json()["method"] == "POST"


def test_rate_limit_triggers_429():
    statuses = [client.get("/tight/echo/x").status_code for _ in range(5)]
    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] == 429 and statuses[4] == 429
    r = client.get("/tight/echo/x")
    assert r.json()["route"] == "tight"


def test_requests_are_logged():
    r = client.get("/admin/logs?limit=50")
    assert r.status_code == 200
    logs = r.json()["logs"]
    assert logs, "expected logged requests"
    routes = {l["route"] for l in logs}
    assert {"echo-api", "tight"} <= routes
    statuses = {l["upstream_status"] for l in logs}
    assert 200 in statuses and 429 in statuses
    assert all("latency_ms" in l and l["latency_ms"] >= 0 for l in logs)


def test_upstream_health_check():
    r = client.get("/admin/health")
    assert r.status_code == 200
    ups = {u["name"]: u for u in r.json()["upstreams"]}
    assert ups["echo-api"]["status"] == "up"
    assert ups["tight"]["status"] == "up"


def test_no_route_404_and_admin_routes():
    assert client.get("/nothing/here").status_code == 404
    r = client.get("/admin/routes")
    assert {x["name"] for x in r.json()["routes"]} == {"echo-api", "tight"}
