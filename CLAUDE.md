# hackton-be

Django 6 ASGI backend. Receives results from the AI process (`../AI`) and streams them to the Next.js frontend (`../hackton-fe`) over WebSocket.

## Commands (uv — do not use pip/venv directly)
- `uv sync` — install deps
- `uv add <pkg>` — add a dependency
- `uv run manage.py migrate`
- `uv run manage.py runserver` — serves ASGI (daphne is first in `INSTALLED_APPS`)
- `uv run daphne config.asgi:application` — production-style server
- `uv run manage.py test` — async WebSocket tests in `stream/tests.py`
- Copy `.env.example` to `.env` for local config

## Architecture
- `config/asgi.py` — `ProtocolTypeRouter`: HTTP -> Django, WebSocket -> Channels.
  - `ws/stream/` browsers, read-only, Origin-checked (`WS_ALLOWED_ORIGINS`, default only `https://hack-nation-fe.vercel.app`; add localhost via `.env` for local dev; CORS uses `CORS_ALLOWED_ORIGINS`). Late joiners get the latest payload on connect.
  - `ws/ingest/?token=<INGEST_TOKEN>` AI process, write-only. No Origin check (not a browser); closes with 4401 on bad token.
- `stream/services.py` — `publish(payload)`: caches latest payload and `group_send`s to group `ai_stream`. Both ingest paths (WS and `POST /api/ingest/` with `X-Ingest-Token`) go through it.
- `telemetry/` — persistence (SQLite) + REST for the engine/dashboard:
  - `GET/POST /api/telemetry/` (last 50 / create), `GET /api/telemetry/latest/` (404 if empty). Model fields: `catfish_count, ph, temperature, turbidity, tds, status, recommendation`.
  - `GET/POST /api/biomass/`, `GET /api/biomass/latest/` (200 `{}` if empty; FCR, feed given, `cost_saved_idr`).
  - A successful telemetry POST is also `publish`ed to `ws/stream/` (mapped to the payload contract below, `level` derived from the `status` prefix: PERINGATAN→warning, SANGAT BAIK→good, else ok). The engine can therefore POST every ~2s and the dashboard updates without polling.
  - Telemetry/biomass POST endpoints have no auth yet (dev only).
- REST: `GET /api/health/`, `GET /api/latest/` (latest payload without `frame`).

## Payload contract
Keep in sync with `../AI/CLAUDE.md` and `../hackton-fe/CLAUDE.md`:
`{frame?: base64 jpeg, count, telemetry: {ph, temp, turbidity, tds}, status, recommendation, level: "ok"|"warning"|"good"}`
The backend passes JSON through unchanged; it does not validate fields.

## Notes
- Run order for the demo: `uv run manage.py runserver` -> `pnpm dev` (FE) -> `python main_engine.py` (AI).
- `DJANGO_ALLOW_ALL` (default 1, temporary) opens ALLOWED_HOSTS, CORS and WS origins to everyone; set 0 to enforce `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` / `WS_ALLOWED_ORIGINS`.
- Without `REDIS_URL`, channel layer and cache are in-memory (single process only). Set `REDIS_URL` for multiple processes/workers.
- Frames are large; the latest payload is cached in full so new viewers see a frame immediately.
- Telegram integration was planned and dropped (also removed from the engine plan) — don't add it unless asked.
- DRF `@api_view` does not support `async def`; use sync views with `async_to_sync` when calling async code.
- Python is 3.13+ (`pyproject.toml`).
