"""In-memory sliding-window rate limiting.

Owns the counters; exposes `RateLimiter`.
"""
from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    """Sliding-window limiter: at most `limit` hits per `window` seconds, per key."""

    def __init__(self, limit: int, window: int) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[object, list[float]] = defaultdict(list)

    def hit(self, key: object, now: float | None = None) -> bool:
        """Record a hit for `key`. Returns True if it is allowed, False if over the limit."""
        current = now if now is not None else time.time()
        timestamps = self._hits[key]
        cutoff = current - self.window
        while timestamps and timestamps[0] <= cutoff:
            timestamps.pop(0)
        if len(timestamps) >= self.limit:
            return False
        timestamps.append(current)
        return True

    def reset(self) -> None:
        """Clear all counters — used by tests between cases."""
        self._hits.clear()
