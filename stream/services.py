"""Shared logic for pushing AI results to browsers."""

from channels.layers import get_channel_layer
from django.core.cache import cache

STREAM_GROUP = "ai_stream"
LATEST_KEY = "stream:latest"

# Payload sent by the AI process (see AI/CLAUDE.md for the full contract):
#   {
#     "frame": "<base64 jpeg, optional>",
#     "count": 12,
#     "telemetry": {"ph": 7.2, "temp": 29.1, "turbidity": 115, "tds": 820},
#     "status": "IDEAL: ...",
#     "recommendation": "...",
#     "level": "ok" | "warning" | "good"
#   }


def latest_payload() -> dict | None:
    return cache.get(LATEST_KEY)


def latest_summary() -> dict | None:
    """Latest payload without the (large) frame, for REST."""
    payload = latest_payload()
    if payload is None:
        return None
    return {k: v for k, v in payload.items() if k != "frame"}


async def publish(payload: dict) -> None:
    """Store as latest and fan out to all browsers."""
    cache.set(LATEST_KEY, payload, timeout=None)

    layer = get_channel_layer()
    await layer.group_send(STREAM_GROUP, {"type": "stream.event", "data": payload})

