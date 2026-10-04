from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.urls import path

from .consumers import IngestConsumer, ViewerConsumer

router = URLRouter(
    [
        path("ws/ingest/", IngestConsumer.as_asgi()),
        path("ws/stream/", ViewerConsumer.as_asgi()),
    ]
)


@override_settings(INGEST_TOKEN="secret")
class StreamTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    async def test_ingest_rejects_bad_token(self):
        comm = WebsocketCommunicator(router, "/ws/ingest/?token=nope")
        connected, code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(code, 4401)

    async def test_ingest_is_broadcast_to_viewer(self):
        viewer = WebsocketCommunicator(router, "/ws/stream/")
        self.assertTrue((await viewer.connect())[0])
        ingest = WebsocketCommunicator(router, "/ws/ingest/?token=secret")
        self.assertTrue((await ingest.connect())[0])

        await ingest.send_json_to({"count": 3, "level": "ok"})
        self.assertEqual(await viewer.receive_json_from(), {"count": 3, "level": "ok"})

        # Late joiner gets the latest state right away.
        late = WebsocketCommunicator(router, "/ws/stream/")
        await late.connect()
        self.assertEqual(await late.receive_json_from(), {"count": 3, "level": "ok"})

        for c in (viewer, ingest, late):
            await c.disconnect()
