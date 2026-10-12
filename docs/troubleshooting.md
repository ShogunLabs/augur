# Troubleshooting

## Compose cannot find database variables

Use the Docker env file explicitly. `env_file` passes values into containers, while `--env-file` also supplies values used when Compose interpolates `docker-compose.yml`:

```bash
cd backend
docker compose --env-file .env.docker up -d --build
```

For Docker, confirm `DB_HOST=postgres`, not `localhost`.

## PostgreSQL is not ready

Check both services and the database logs:

```bash
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs postgres
```

Wait until PostgreSQL reports `healthy`, then apply migrations:

```bash
docker compose --env-file .env.docker exec backend alembic upgrade head
```

The host port is `5433`; the backend uses `postgres:5432` inside the Compose network.

## The API returns `DATABASE_NOT_READY`

Check readiness and the backend logs:

```bash
curl http://127.0.0.1:8000/ready
docker compose --env-file .env.docker logs backend
```

If the schema has not been created, run `alembic upgrade head` in the backend container.

## Sync fails because the Upstox token is missing or invalid

Set `UPSTOX_ACCESS_TOKEN` in the active `.env` or `.env.docker`, then check the upstream health endpoint:

```bash
curl http://127.0.0.1:8000/health/upstox
```

A failed response means the configured token or Upstox reachability needs attention. Discovery and hydration use the same shared client and retry transient `429` and `5xx` responses.

## Hydration reports failures

Inspect the failure sidecar:

```bash
cat backend/hydration_failures.json
```

Retry only the recorded IDs after correcting the upstream or configuration issue:

```bash
cd backend
python sync.py --retry-failed
```

With Docker:

```bash
docker compose --env-file .env.docker exec backend python sync.py --retry-failed
```

## A targeted sync does not work

`--only` accepts one of the four current statuses:

```text
upcoming, open, closed, listed
```

Example:

```bash
python sync.py --only open
```

This hydrates the existing `backend/ipos/open.json` snapshot without running discovery.

## The frontend shows local preview data

The frontend falls back to a small local preview when its API request fails. Start the backend on port 8000, then start Vite from `frontend/`; its dev proxy forwards `/api`, `/health`, and `/ready` to the backend.

If the API uses another URL, set:

```bash
VITE_API_URL=https://api.example.test npm run dev
```

For a browser CORS error, add the frontend origin to `CORS_ORIGINS` and restart the backend.

## Port 8000, 5173, or 5433 is already in use

Find the process or container using the port, then stop it or change the local mapping. The standard local ports are:

```text
API       8000
Frontend  5173
Postgres  5433
```

Vite automatically chooses another development port when 5173 is occupied; use the printed URL.

## Day-end export fails with a missing file

`batch_worker.py` reads all four staging files. Run discovery first:

```bash
python get_ipos.py
python batch_worker.py
```

The generated files appear under `backend/exports/daily/YYYY-MM-DD/`.

## Native setup cannot connect to PostgreSQL

Native development uses `DB_HOST=localhost` and the port configured in `.env`. Confirm PostgreSQL is running, the role and database exist, and the configured credentials match. Docker development is separate and uses its own PostgreSQL volume and `DB_HOST=postgres`.
