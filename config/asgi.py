"""
ASGI config. HTTP goes to Django, WebSockets go to Channels routing:

    /ws/stream/  -> browsers (Next.js), Origin-checked, read-only
    /ws/ingest/  -> AI process, token-checked, write-only
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Must run before importing anything that touches models/consumers.
django_asgi_app = get_asgi_application()

from django.urls import path  # noqa: E402

from stream.consumers import IngestConsumer, ViewerConsumer  # noqa: E402

websocket_router = URLRouter(
    [
        # The AI process is not a browser and sends no Origin header, so it
        # is authenticated by token inside the consumer instead.
        path("ws/ingest/", IngestConsumer.as_asgi()),
        path(
            "ws/stream/",
            OriginValidator(ViewerConsumer.as_asgi(), settings.WS_ALLOWED_ORIGINS),
        ),
    ]
)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": websocket_router,
    }
)
