# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

Augur is an **IPO data system** with a FastAPI/PostgreSQL backend under `backend/` and a Vite/React frontend under `frontend/`. Documentation lives in the root `README.md` and `docs/`. Work happens on the `development-branch`; `main` is the PR target.

## Commands (run from `backend/`)

The venv already exists at `backend/.venv`. Activate it before running anything:
```bash
source .venv/bin/activate
```

- **Start the API** (native): `uvicorn app.main:app --host 0.0.0.0 --port 8000` → docs at `http://127.0.0.1:8000/docs`
- **Run the full sync** (Upstox discovery → JSON staging → hydration → PostgreSQL): `python sync.py`
- **Hydrate one lifecycle status without re-discovering**: `python sync.py --only open` or `python hydrate_ipos.py --only open`
- **Retry only previously-failed IPOs** (reads `hydration_failures.json`): `python sync.py --retry-failed` or `python hydrate_ipos.py --retry-failed`
- **Generate day-end exports** (JSON/CSV/XLSX into `exports/daily/<date>/`): `python batch_worker.py`
- **Run tests**: `pytest -q` (unit only) or `RUN_INTEGRATION_TESTS=1 pytest -q` (needs reachable PostgreSQL)
- **Run a single test**: `pytest tests/test_ipos.py -q`
- **Apply migrations**: `alembic upgrade head`
- **Create a migration after model changes**: `alembic revision --autogenerate -m "describe change"`
- **Docker**: from `backend/`, configure `.env.docker`, then run `docker compose --env-file .env.docker up -d`, `docker compose --env-file .env.docker exec backend alembic upgrade head`, and `docker compose --env-file .env.docker exec backend python sync.py`. DB is exposed on host port `5433` (service name `postgres` inside compose).
- **Frontend** (run from `frontend/`): `npm install`, `npm run dev`, `npm run build`. The Vite dev server proxies API requests to `http://127.0.0.1:8000`.

## Architecture (big picture)

Four stages, each independently checkable:

1. **Discovery** — `get_ipos.py` calls Upstox `GET /v2/ipos` (paginated, 8 status × issue-type combos) and writes four JSON staging files in `backend/ipos/`: `open.json`, `closed.json`, `upcoming.json`, `listed.json`.
2. **Hydration** — `hydrate_ipos.py` reads those files, collects unique IPO IDs, calls `GET /v2/ipos/{id}` concurrently (`asyncio` + `httpx.AsyncClient`, concurrency 10, chunked commits 20), normalizes the response, and UPSERTs into PostgreSQL. Idempotent — re-running creates no duplicates. Writes failures to `hydration_failures.json`.
3. **Storage** — SQLAlchemy model `app/models.py` (`ipos` table, one table for both `regular` and `sme`, distinguished by `issue_type`). JSONB columns preserve `timeline`, `registrar_info`, and the full `raw_data` payload. Alembic migrations in `migrations/versions/`.
4. **API** — FastAPI app in `app/main.py`. Routes under `app/api/routes/`. Business logic in `app/services/`, DB queries in `app/repositories/`, public contracts in `app/schemas/`. Common error format `{error: {code, message, details}}` handled in `app/api/exception_handlers.py`.

The API only reads from PostgreSQL; clients never touch Upstox or the JSON files directly. `batch_worker.py` reads the JSON staging files only — it does not fetch upstream data.

## Key conventions

- **Statuses**: `upcoming`, `open`, `closed`, `listed`. **Issue types**: `regular`, `sme`. Enforced by CheckConstraints on the model.
- **API responses omit `null` fields** (`response_model_exclude_none=True`) so the frontend can render missing values as `-`.
- **Serialization reads from `raw_data`** (the preserved Upstox payload), not from model columns — `app/services/ipo.py` `serialize_ipo_list` / `serialize_ipo_detail`.
- **Config via env vars** (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `UPSTOX_ACCESS_TOKEN`, `CORS_ORIGINS`). Native dev uses `.env` (`DB_HOST=localhost`); Docker uses `.env.docker` (`DB_HOST=postgres`). Never commit `.env` / `.env.docker` — only `.env.example`.
- **Tests** use a `TestClient` fixture in `tests/conftest.py`; tests marked `integration` require a live DB (gated by `RUN_INTEGRATION_TESTS`). `pytest -q` is green on a fresh checkout without `.env`.

## New API endpoints

- `GET /health/upstox` — verifies Upstox token is valid at deploy time (5s timeout, no retries).
- `GET /api/v1/ipos?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` — date-range filter on `bidding_start_date` (backed by index `ix_ipos_status_bidding_start_date`).

## Upstox client (shared, `app/integrations/upstox.py`)

- **Rate limiting**: `REQUEST_RATE = 10/s` paces requests so Upstox never sees a burst worth throttling (10 rps = 600 rpm).
- **Sync retry**: `with_retry()` — sync path used by `get_ipos.py` (`httpx.Client`). Exponential backoff + jitter, honors `Retry-After`.
- **Async retry**: `with_retry_async()` — async path used by `hydrate_ipos.py` (`httpx.AsyncClient`). Awaits inside the loop so `raise_for_status()` actually triggers retry.
- **Health check**: `is_reachable()` — fast fail (5s, no retries) for `GET /health/upstox`.

## Sync + retry behavior

```bash
python sync.py                      # full pipeline: discovery → hydration → PostgreSQL
python sync.py --only open          # hydrate one lifecycle slice, no re-discovery
python sync.py --retry-failed       # retry ONLY failed IPOs from hydration_failures.json
python hydrate_ipos.py --retry-failed
```

- `hydration_failures.json` is **always rewritten** on a `--retry-failed` run, so previously-succeeded IDs don't linger.
- On a clean full run with zero failures, the file is left untouched (no pointless writes).

## Deferred scope (do not build yet)

Allotment checking, registrar adapters, DRHP/RHP ingestion, RAG/IPO insights, auth, watchlists/notifications, Android app, CI/CD. Keep these isolated from the v1 data/API layer when they eventually land.

## Notes

- Python 3.13, PostgreSQL 17, FastAPI, SQLAlchemy, Alembic, httpx, asyncpg, xlsxwriter.
- `UPSTOX_ACCESS_TOKEN` is required to run `sync.py` / `get_ipos.py` / `hydrate_ipos.py` — these exit with a clear error if it's missing.
- `backend/.env.example` is the committed, safe placeholder file.
- Shared Upstox client in `app/integrations/upstox.py` centralizes auth, retries, and reachability.
