# Quick start

This guide starts the complete local stack: PostgreSQL, the FastAPI backend, the IPO data sync, and the Vite frontend.

## Recommended: Docker

### Prerequisites

- Docker with Compose support.
- Node.js and npm.
- A valid Upstox access token.

### Configure the backend

From the repository root:

```bash
cp backend/.env.example backend/.env.docker
```

Edit `backend/.env.docker` and set real values. For Docker, use the Compose service name for the database host:

```env
UPSTOX_ACCESS_TOKEN=your_upstox_access_token

DB_HOST=postgres
DB_PORT=5432
DB_NAME=augur_project
DB_USER=ipo_user
DB_PASSWORD=your_password

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Do not commit `.env.docker` or `.env`; use `backend/.env.example` as the safe template.

### Start PostgreSQL and the API

```bash
cd backend
docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker ps
```

Apply the schema:

```bash
docker compose --env-file .env.docker exec backend alembic upgrade head
```

Populate the database from Upstox:

```bash
docker compose --env-file .env.docker exec backend python sync.py
```

Verify the services:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Expected responses are `{"status":"ok"}` and `{"status":"ready","database":"ok"}`.

### Start the frontend

In a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. The Vite dev server proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8000`.

If the API is hosted elsewhere, set `VITE_API_URL` before starting Vite:

```bash
VITE_API_URL=https://api.example.test npm run dev
```

When the API cannot be reached, the frontend shows its local preview data and marks the connection as unavailable.

## Native backend setup

Use this path when Python and PostgreSQL are installed on the host.

### Prerequisites

- Python 3.13 or newer.
- PostgreSQL 17 or a compatible supported version.
- Git and a valid Upstox access token.

### Install and configure

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Edit `.env` with host-native database settings:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=augur_project
DB_USER=ipo_user
DB_PASSWORD=your_password
UPSTOX_ACCESS_TOKEN=your_upstox_access_token
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Create the configured PostgreSQL role and database, for example:

```bash
sudo -u postgres psql -d postgres
```

```sql
CREATE USER ipo_user WITH PASSWORD 'your_password';
CREATE DATABASE augur_project OWNER ipo_user;
```

Then run:

```bash
alembic upgrade head
python sync.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The interactive API documentation is available at <http://127.0.0.1:8000/docs>.

## Stop Docker services

From `backend/`:

```bash
docker compose --env-file .env.docker down
```

Use `docker compose --env-file .env.docker down -v` only when the local PostgreSQL volume and its data can be removed.
