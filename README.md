# Augur

Augur collects Indian IPO data from Upstox, stages and hydrates it into PostgreSQL, exposes it through a FastAPI API, and provides a Vite/React market board.

## Key features

- Upstox discovery for upcoming, open, closed, and listed IPOs.
- Detailed IPO hydration with idempotent PostgreSQL upserts.
- FastAPI health, homepage, list, and detail endpoints.
- Filtering, sorting, pagination, regular/SME support, and date-range queries.
- Docker Compose setup plus JSON, CSV, and XLSX day-end exports.

## Prerequisites

- Docker and Docker Compose for the recommended setup.
- A valid Upstox access token for discovery and hydration.
- Node.js and npm for the frontend.
- Native setup additionally requires Python 3.13+ and PostgreSQL.

## Quick start

```bash
cp backend/.env.example backend/.env.docker
# Edit backend/.env.docker and set UPSTOX_ACCESS_TOKEN and database values.

cd backend
docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker exec backend alembic upgrade head
docker compose --env-file .env.docker exec backend python sync.py
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

- Frontend: <http://127.0.0.1:5173>
- API: <http://127.0.0.1:8000>
- API docs: <http://127.0.0.1:8000/docs>

## Documentation

- [Quick start](docs/quick-start.md) — setup, configuration, Docker, native development, and running the apps.
- [Architecture](docs/architecture.md) — components, storage, and data flow.
- [Usage](docs/usage.md) — commands, API examples, sync, retries, and exports.
- [Development](docs/development.md) — project structure, tests, migrations, and contribution practices.
- [Troubleshooting](docs/troubleshooting.md) — common setup, Docker, API, hydration, and frontend issues.
