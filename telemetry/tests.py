from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from config.asgi import application

from .models import TelemetryLog

SAMPLE = {
    "catfish_count": 12,
    "ph": 8.6,
    "temperature": 30.8,
    "turbidity": 285,
    "tds": 980,
    "status": "PERINGATAN: Air Keruh",
    "recommendation": "Tunda Pakan",
}


class TelemetryApiTests(TransactionTestCase):
    def test_post_saves_lists_and_latest(self):
        c = APIClient()
        self.assertEqual(c.get("/api/telemetry/latest/").status_code, 404)
        self.assertEqual(c.post("/api/telemetry/", SAMPLE, format="json").status_code, 201)
        self.assertEqual(TelemetryLog.objects.count(), 1)
        self.assertEqual(len(c.get("/api/telemetry/").json()), 1)
        self.assertEqual(c.get("/api/telemetry/latest/").json()["ph"], 8.6)

    def test_post_validates(self):
        r = APIClient().post("/api/telemetry/", {"ph": 7}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_biomass(self):
        c = APIClient()
        self.assertEqual(c.get("/api/biomass/latest/").json(), {})
        body = {"feed_given_kg": 2.0, "fcr_value": 1.4, "cost_saved_idr": 3600}
        self.assertEqual(c.post("/api/biomass/", body, format="json").status_code, 201)
        self.assertEqual(c.get("/api/biomass/latest/").json()["total_fish_count"], 250)

    @override_settings(INGEST_TOKEN="secret")
    def test_http_ingest_requires_token(self):
        c = APIClient()
        self.assertEqual(c.post("/api/ingest/", {"count": 1}, format="json").status_code, 401)
        r = c.post("/api/ingest/", {"count": 1}, format="json", headers={"X-Ingest-Token": "secret"})
        self.assertEqual(r.status_code, 202)


class TelemetryBroadcastTests(TransactionTestCase):
    async def test_post_is_pushed_to_websocket_viewer(self):
        viewer = WebsocketCommunicator(
            application, "/ws/stream/", headers=[(b"origin", b"https://hack-nation-fe.vercel.app")]
        )
        self.assertTrue((await viewer.connect())[0])
        resp = await sync_to_async(APIClient().post)("/api/telemetry/", SAMPLE, format="json")
        self.assertEqual(resp.status_code, 201)
        msg = await viewer.receive_json_from()
        self.assertEqual(msg["level"], "warning")
        self.assertEqual(msg["telemetry"]["temp"], 30.8)
        await viewer.disconnect()
