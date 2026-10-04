import hmac

from asgiref.sync import async_to_sync
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import latest_summary, publish


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def latest(request):
    """Latest AI result without the frame (handy for polling/debugging)."""
    return Response(latest_summary())


@api_view(["POST"])
def ingest(request):
    """HTTP alternative to /ws/ingest/ for one-off pushes from the AI process."""
    token = request.headers.get("X-Ingest-Token", "")
    if not hmac.compare_digest(token, settings.INGEST_TOKEN):
        return Response({"detail": "unauthorized"}, status=401)
    if not isinstance(request.data, dict):
        return Response({"detail": "payload must be an object"}, status=400)
    async_to_sync(publish)(dict(request.data))
    return Response({"status": "accepted"}, status=202)
