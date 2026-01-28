"""Simple in-memory debug store for recording fallbacks and raw request/response samples.

This is intentionally simple: a process-local list with append/get helpers. It's suitable for
debugging during development and for returning the last N events via a debug endpoint.
"""
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List

_lock = Lock()
_events: List[Dict[str, Any]] = []


def record_fallback(event: Dict[str, Any]):
    """Record a fallback event. Event should be JSON-serializable."""
    e = dict(event)
    e.setdefault('timestamp', datetime.utcnow().isoformat() + 'Z')
    with _lock:
        _events.append(e)
        # keep last 100 events
        if len(_events) > 100:
            del _events[0: len(_events) - 100]


def get_fallbacks(limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        return list(_events[-limit:])[::-1]
