"""Token-bucket rate limiter, per route + client IP. In-memory, stdlib only."""
import threading
import time


class RateLimiter:
    def __init__(self):
        self._buckets: dict[tuple[str, str], list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, route_name: str, client_ip: str, capacity: int, refill_per_sec: float) -> bool:
        key = (route_name, client_ip)
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (float(capacity), now))
            tokens = min(capacity, tokens + (now - last) * refill_per_sec)
            if tokens >= 1.0:
                self._buckets[key] = (tokens - 1.0, now)
                return True
            self._buckets[key] = (tokens, now)
            return False
