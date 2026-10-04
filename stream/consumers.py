import hmac
import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from .services import STREAM_GROUP, latest_payload, publish


class ViewerConsumer(AsyncWebsocketConsumer):
    """Browser side: receives the live AI stream. Client messages are ignored."""

    async def connect(self):
        await self.channel_layer.group_add(STREAM_GROUP, self.channel_name)
        await self.accept()
        # Give late joiners the current state immediately.
        latest = latest_payload()
        if latest is not None:
            await self.send(text_data=json.dumps(latest))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(STREAM_GROUP, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def stream_event(self, event):
        await self.send(text_data=json.dumps(event["data"]))


class IngestConsumer(AsyncWebsocketConsumer):
    """AI side: connect with ?token=... and send one JSON payload per message."""

    async def connect(self):
        query = parse_qs(self.scope["query_string"].decode())
        token = (query.get("token") or [""])[0]
        if not hmac.compare_digest(token, settings.INGEST_TOKEN):
            await self.close(code=4401)
            return
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "invalid json"}))
            return
        if not isinstance(payload, dict):
            await self.send(text_data=json.dumps({"error": "payload must be an object"}))
            return
        await publish(payload)
