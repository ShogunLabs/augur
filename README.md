# Augur Backend

Backend data-ingestion layer for the Augur IPO project.

## Current Scope

At this stage the backend:

1. Fetches IPO summaries from the Upstox `/v2/ipos` endpoint.
2. Stores those summaries in four JSON files grouped by IPO status.
3. Reads the IPO IDs from those JSON files.
4. Fetches complete IPO details from `/v2/ipos/{id}`.
5. Stores the hydrated data in PostgreSQL using SQLAlchemy.
6. Uses Alembic to version and reproduce the database schema.

The FastAPI API layer and allotment-checking layer are not implemented yet.

## Architecture

```text
                         Upstox API
                             |
                             v
                        GET /v2/ipos
                             |
                       get_ipos.py
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
      open.json         closed.json       upcoming.json
          |                  |                  |
          +------------------+------------------+
                             |
                         listed.json
                             |
                             v
                      hydrate_ipos.py
                             |
                      Extract IPO IDs
                             |
                             v
                    GET /v2/ipos/{id}
                             |
                             v
                      Full IPO details
                             |
                             v
                         SQLAlchemy
                             |
                             v
                       PostgreSQL
                         augur_project
                             |
                             v
                           ipos
```

The JSON files are staging/snapshot data from `/v2/ipos`. PostgreSQL is the canonical datastore for hydrated IPO information.

## Project Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── database.py
│   └── models.py
│
├── ipos/
│   ├── open.json
│   ├── closed.json
│   ├── upcoming.json
│   └── listed.json
│
├── migrations/
│   ├── versions/
│   │   └── <initial migration>.py
│   ├── env.py
│   ├── script.py.mako
│   └── README
│
├── .env
├── .env.example
├── alembic.ini
├── get_ipos.py
├── hydrate_ipos.py
├── requirements.txt
├── .gitignore
└── README.md
```

Never commit `.env` or the Upstox access token.

## Prerequisites

Recommended environment:

- Linux/Debian/Ubuntu
- Python 3.13+
- PostgreSQL 17+
- Git

Python dependencies currently include:

- SQLAlchemy 2.x
- Psycopg 3
- Alembic
- httpx
- python-dotenv

## 1. Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd augur/backend
```

## 2. Create the Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the dependency file is not available yet:

```bash
pip install sqlalchemy 'psycopg[binary]' alembic httpx python-dotenv
```

## 3. PostgreSQL Setup

Check PostgreSQL:

```bash
sudo systemctl status postgresql
pg_lsclusters
```

The PostgreSQL cluster should be `online` on port `5432`.

Create the application role and database:

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE ipo_user LOGIN PASSWORD 'YOUR_PASSWORD';
CREATE DATABASE augur_project OWNER ipo_user;
```

If the role already exists, reset its password:

```sql
\password ipo_user
```

Verify:

```sql
\du
\l
```

Exit:

```sql
\q
```

Test the database login:

```bash
psql -U ipo_user -h localhost -d augur_project -W
```

Inside `psql`:

```sql
\conninfo
```

Expected database/user:

```text
augur_project / ipo_user
```

## 4. Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Configure:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=augur_project
DB_USER=ipo_user
DB_PASSWORD=YOUR_PASSWORD

UPSTOX_ACCESS_TOKEN=YOUR_UPSTOX_ACCESS_TOKEN
```

Do not commit `.env`.

## 5. Test SQLAlchemy

```bash
python3 -c "from app.database import engine; c=engine.connect(); print('Database connection: OK'); c.close()"
```

Expected:

```text
Database connection: OK
```

Verify the loaded non-secret settings:

```bash
python3 -c "from app.database import DB_HOST, DB_PORT, DB_NAME, DB_USER; print(DB_HOST, DB_PORT, DB_NAME, DB_USER)"
```

Expected:

```text
localhost 5432 augur_project ipo_user
```

## 6. Create the Database Schema

The SQLAlchemy model is in:

```text
app/models.py
```

The current database has one main table:

```text
ipos
```

Regular and SME IPOs share the same table and are distinguished by:

```text
issue_type = regular | sme
```

IPO lifecycle status is:

```text
upcoming | open | closed | listed
```

Nested Upstox data is also preserved:

- `timeline` → JSONB
- `registrar_info` → JSONB
- `raw_data` → complete `/ipos/{id}` payload as JSONB

Apply all committed migrations:

```bash
alembic upgrade head
```

Verify the schema:

```bash
psql -U ipo_user -h localhost -d augur_project -W
```

```sql
\dt
\d ipos
```

You should see:

```text
alembic_version
ipos
```

## 7. Fetch IPO Summary Data

`get_ipos.py` only handles the list endpoint.

It fetches all combinations of:

```text
upcoming + regular
upcoming + sme
open + regular
open + sme
closed + regular
closed + sme
listed + regular
listed + sme
```

Pagination is handled by the script.

The resulting summaries are written to:

```text
ipos/open.json
ipos/closed.json
ipos/upcoming.json
ipos/listed.json
```

Run:

```bash
python3 get_ipos.py
```

These files contain the list-level fields needed to identify an IPO, especially the Upstox `id`.

## 8. Hydrate Full IPO Details

`hydrate_ipos.py` reads the four existing JSON files. It does not create another set of JSON files.

Flow:

```text
open.json
closed.json
upcoming.json
listed.json
      |
      v
unique IPO IDs
      |
      v
GET /v2/ipos/{id}
      |
      v
normalize full response
      |
      v
PostgreSQL UPSERT
```

Run:

```bash
python3 hydrate_ipos.py
```

For each IPO the script:

1. Fetches the complete `/v2/ipos/{id}` record.
2. Converts dates/times/numeric values to PostgreSQL-compatible types.
3. Stores queryable fields in regular PostgreSQL columns.
4. Stores `timeline` as JSONB.
5. Stores `registrar_info` as JSONB.
6. Stores the original `data` object as `raw_data` JSONB.
7. UPSERTs using `ipos.id` as the primary key.

Repeated runs do not create duplicate IPO rows.

## 9. Verify the Data

Count rows:

```sql
SELECT COUNT(*) FROM ipos;
```

View recent records:

```sql
SELECT
    id,
    symbol,
    name,
    status,
    issue_type,
    listing_date
FROM ipos
ORDER BY first_seen_at DESC
LIMIT 10;
```

View status/type distribution:

```sql
SELECT
    status,
    issue_type,
    COUNT(*)
FROM ipos
GROUP BY status, issue_type
ORDER BY status, issue_type;
```

Inspect registrar JSON:

```sql
SELECT id, registrar_info
FROM ipos
LIMIT 5;
```

Inspect the preserved raw Upstox payload:

```sql
SELECT
    id,
    raw_data->>'symbol' AS symbol,
    raw_data->>'name' AS name
FROM ipos
LIMIT 5;
```

## 10. Database Migrations

The project uses Alembic for schema versioning.

After changing `app/models.py`:

```bash
alembic revision --autogenerate -m "describe the change"
```

Review the generated migration in:

```text
migrations/versions/
```

Then apply it:

```bash
alembic upgrade head
```

Useful commands:

```bash
alembic current
alembic history
```

Migration files under `migrations/versions/` should be committed to Git.

## Reproduce the Current State on Another Server

After installing PostgreSQL:

```bash
git clone <REPOSITORY_URL>
cd augur/backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Configure `.env`, create the `ipo_user` PostgreSQL role and `augur_project` database, then run:

```bash
alembic upgrade head
python3 get_ipos.py
python3 hydrate_ipos.py
```

Verify:

```bash
psql -U ipo_user -h localhost -d augur_project -W
```

```sql
SELECT COUNT(*) FROM ipos;
```

At this point the current ingestion/database stage is reproduced.

## Current Development Flow

```text
Upstox /v2/ipos
        |
        v
get_ipos.py
        |
        v
open.json / closed.json / upcoming.json / listed.json
        |
        v
hydrate_ipos.py
        |
        v
Upstox /v2/ipos/{id}
        |
        v
PostgreSQL ipos table
```

## Current Scope

Implemented:

- PostgreSQL database
- SQLAlchemy database layer
- IPO SQLAlchemy model
- Alembic migrations
- Upstox `/v2/ipos` ingestion
- status-based JSON staging
- Upstox `/v2/ipos/{id}` hydration
- PostgreSQL UPSERT
- raw and nested JSON preservation

Not implemented yet:

- FastAPI endpoints
- `/health`
- registrar-specific allotment checker
- background scheduler
- caching
- authentication/authorization
- frontend
