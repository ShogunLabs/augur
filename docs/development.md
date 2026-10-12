# Development

## Repository structure

```text
augur/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route handlers
│   │   ├── integrations/     # Upstox client and retry logic
│   │   ├── repositories/     # Database queries
│   │   ├── schemas/          # Public API models
│   │   └── services/         # Application logic and serialization
│   ├── migrations/           # Alembic migrations
│   ├── tests/                # API and integration tests
│   ├── ipos/                 # Generated staging snapshots
│   ├── exports/              # Generated day-end exports
│   ├── get_ipos.py           # Discovery
│   ├── hydrate_ipos.py       # Detail hydration
│   ├── sync.py               # Discovery + hydration orchestration
│   ├── batch_worker.py       # JSON/CSV/XLSX exports
│   ├── docker-compose.yml
│   └── Dockerfile
├── frontend/
│   ├── src/main.jsx          # Vite/React application
│   ├── src/styles.css        # Frontend styling
│   ├── vite.config.js        # Dev server and API proxy
│   └── package.json
├── docs/
└── README.md
```

Generated snapshots, exports, failure logs, and local environment files are runtime artifacts. Do not add credentials to the repository.

## Development setup

The fastest development loop is Docker for the backend and Vite for the frontend:

```bash
cd backend
docker compose --env-file .env.docker up -d
docker compose --env-file .env.docker exec backend alembic upgrade head
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

For native backend work, create `backend/.venv`, install `backend/requirements-dev.txt`, and configure `backend/.env` as described in the [quick start](quick-start.md#native-backend-setup).

## Tests

Run the backend test suite from `backend/`:

```bash
pytest -q
```

Integration tests are skipped unless a database is reachable and the flag is set:

```bash
RUN_INTEGRATION_TESTS=1 pytest -q
```

When using the production Docker image, install development dependencies in the running container before testing:

```bash
docker compose --env-file .env.docker exec backend pip install -r requirements-dev.txt
docker compose --env-file .env.docker exec -e RUN_INTEGRATION_TESTS=1 backend pytest -q
```

Build the frontend before submitting UI changes:

```bash
cd frontend
npm run build
```

## Database changes

After changing `backend/app/models.py`, create and review a migration:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Keep migrations under `backend/migrations/versions/` and verify them against the Docker PostgreSQL service when possible.

## Contribution guidelines

- Work on `development-branch`; `main` is the pull-request target.
- Keep external API calls in `backend/app/integrations/` and database queries in repositories.
- Keep public response models in `backend/app/schemas/` separate from SQLAlchemy models.
- Add or update tests for behavior changes and run the relevant backend test command.
- Run `npm run build` for frontend changes.
- Update the relevant file in `docs/` when commands, paths, or API behavior change.
- Never commit `.env`, `.env.docker`, access tokens, generated exports, or local database data.
- Keep changes focused; avoid adding infrastructure or dependencies without a concrete need.
