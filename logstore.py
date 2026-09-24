"""SQLite request log for the gateway."""
import os
import sqlite3
import time

DB_PATH = os.environ.get("GATEWAY_DB",
                          os.path.join(os.path.dirname(__file__), "gateway_logs.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS request_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    client_ip TEXT,
    method TEXT,
    path TEXT,
    route TEXT,
    upstream_status INTEGER,
    latency_ms REAL
);
CREATE INDEX IF NOT EXISTS idx_log_ts ON request_log(ts);
"""


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.executescript(SCHEMA)


def log_request(client_ip, method, path, route, upstream_status, latency_ms):
    with _conn() as c:
        c.execute(
            "INSERT INTO request_log (ts, client_ip, method, path, route, upstream_status, latency_ms)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (time.time(), client_ip, method, path, route, upstream_status, latency_ms),
        )


def recent_logs(limit: int = 100) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM request_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
