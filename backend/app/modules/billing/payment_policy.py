from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone


def effective_status(status, period_end, *, now=None):
    """Deny paid access when an active/trial period has no valid end."""
    value = getattr(status, "value", status)
    if value not in {"active", "trialing"}:
        return value
    if period_end is None:
        return "unpaid"
    if period_end.tzinfo is None:
        period_end = period_end.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return value if period_end > now else "unpaid"


def verify_event(payload: bytes, signature: str, secret: str, *, now=None):
    if not secret:
        raise ValueError("Webhook signing secret is not configured.")
    values = {}
    for part in signature.split(","):
        key, separator, value = part.partition("=")
        if separator:
            values.setdefault(key, []).append(value)
    timestamps = values.get("t", [])
    if len(timestamps) != 1:
        raise ValueError("Invalid webhook timestamp.")
    timestamp = int(timestamps[0])
    if abs((time.time() if now is None else now) - timestamp) > 300:
        raise ValueError("Webhook timestamp is outside the allowed window.")
    expected = hmac.new(
        secret.encode(), timestamps[0].encode() + b"." + payload,
        hashlib.sha256,
    ).hexdigest()
    if not any(hmac.compare_digest(expected, item)
               for item in values.get("v1", [])):
        raise ValueError("Invalid webhook signature.")
    event = json.loads(payload)
    if not isinstance(event, dict) or not isinstance(event.get("id"), str):
        raise ValueError("Invalid webhook event.")
    return event


def feature_for_route(path: str, method: str):
    """Classify the matched FastAPI route, never user-controlled query text."""
    parts = path.strip("/").split("/")
    if "workspaces" not in parts:
        return None
    index = parts.index("workspaces") + 2
    tail = parts[index:]
    if not tail:
        return None
    resource = tail[0]
    if resource in {"live-monitoring", "meetings"} and tail[-1] in {"end", "cancel", "deny", "fail"}:
        return None
    if resource == "channels" and tail[-1] in {"leave", "stop"}:
        return None
    if resource == "monitoring-admin" and tail[-1] == "retention-cleanup":
        return None
    if resource == "live-monitoring" and method.upper() == "DELETE":
        return None
    if resource == "integrations" and len(tail) > 1 and tail[1] == "reports":
        return "reports"
    return {
        "payroll": "payroll",
        "reports": "reports",
        "meetings": "meetings",
        "channels": "channels",
        "analytics": "reports",
        "productivity-insights": "reports",
        "employee-monitoring": "monitoring",
        "monitoring-control": "monitoring",
        "monitoring-admin": "monitoring",
        "live-monitoring": "live_screen",
    }.get(resource)


def workspace_cleanup_route(path: str, method: str) -> bool:
    """Allow authenticated users to STOP existing activity even after expiry."""
    parts = path.strip('/').split('/')
    if 'workspaces' not in parts:
        return False
    tail = parts[parts.index('workspaces') + 2:]
    if not tail:
        return False
    if method.upper() == 'POST':
        return ((tail[0] in {'live-monitoring', 'meetings'} and tail[-1] in {'end', 'cancel', 'deny', 'fail'}) or
                (tail[0] == 'channels' and tail[-1] in {'leave', 'stop'}))
    return method.upper() == 'DELETE' and tail[0] == 'live-monitoring'
