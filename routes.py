"""YAML routing table loader."""
import os

import yaml

CONFIG_PATH = os.environ.get("GATEWAY_ROUTES", os.path.join(os.path.dirname(__file__), "routes.yaml"))


def parse_rate(spec: str):
    """'100/minute' -> (capacity, refill_per_second)."""
    n, _, per = spec.partition("/")
    n = int(n.strip())
    per = per.strip().lower()
    seconds = {"second": 1, "minute": 60, "hour": 3600}.get(per.rstrip("s"), 60)
    return n, n / seconds


def load_routes(path: str = CONFIG_PATH) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    routes = []
    for r in data.get("routes", []):
        capacity, refill = parse_rate(r.get("rate_limit", "100/minute"))
        routes.append({
            "name": r["name"],
            "path_prefix": r["path_prefix"],
            "target": r["target"].rstrip("/"),
            "strip_prefix": r.get("strip_prefix", True),
            "rate_limit": r.get("rate_limit", "100/minute"),
            "capacity": capacity,
            "refill_per_sec": refill,
        })
    # longest prefix first so nested routes match correctly
    routes.sort(key=lambda r: len(r["path_prefix"]), reverse=True)
    return routes
