# Usage

Run backend commands from `backend/`. For Docker commands, keep `--env-file .env.docker` on the Compose command so the service variables are available on a clean checkout.

## Synchronization workflows

Run discovery and hydrate all staged IPOs:

```bash
python sync.py
```

The full pipeline is:

```text
Upstox list API → backend/ipos/*.json → Upstox detail API → PostgreSQL
```

Hydrate one lifecycle status without running discovery again:

```bash
python sync.py --only open
python sync.py --only upcoming
python sync.py --only closed
python sync.py --only listed
```

Retry only IDs in `hydration_failures.json`:

```bash
python sync.py --retry-failed
```

The lower-level scripts are also available:

```bash
python get_ipos.py
python hydrate_ipos.py
python hydrate_ipos.py --only open
python hydrate_ipos.py --retry-failed
```

`get_ipos.py` only refreshes the status snapshots. `hydrate_ipos.py` reads those snapshots and writes to PostgreSQL.

Docker equivalents:

```bash
docker compose --env-file .env.docker exec backend python sync.py
docker compose --env-file .env.docker exec backend python sync.py --only open
docker compose --env-file .env.docker exec backend python sync.py --retry-failed
```

## API examples

With the backend running on port 8000:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/health/upstox
curl http://127.0.0.1:8000/api/v1/home?limit=10
```

List IPOs with filters and pagination:

```bash
curl 'http://127.0.0.1:8000/api/v1/ipos?status=open&issue_type=sme&limit=20'
curl 'http://127.0.0.1:8000/api/v1/ipos?status=listed&sort=listing_date&page=1&limit=20'
curl 'http://127.0.0.1:8000/api/v1/ipos?from_date=2026-09-01&to_date=2026-09-30'
```

The list endpoint accepts:

```text
status=upcoming|open|closed|listed
issue_type=regular|sme
sort=newest|listing_date|bidding_start_date|bidding_end_date
page=1..n
limit=1..100
from_date=YYYY-MM-DD
to_date=YYYY-MM-DD
```

Fetch one detailed record using its ID from the list response:

```bash
curl 'http://127.0.0.1:8000/api/v1/ipos/<ipo_id>'
```

FastAPI also publishes an interactive contract at <http://127.0.0.1:8000/docs>.

## Frontend workflows

From `frontend/`:

```bash
npm run dev
npm run build
npm run preview
```

The market board supports:

- lifecycle status filters;
- regular/SME filtering;
- text search by issue, symbol, or industry;
- sorting by newest, bidding dates, or listing date;
- pagination across the full API list; and
- an IPO detail drawer backed by `/api/v1/ipos/{ipo_id}`.

## Day-end exports

Generate files from the current JSON snapshots:

```bash
python batch_worker.py
```

The files are written to `backend/exports/daily/YYYY-MM-DD/`:

```text
ipos.json
ipos.csv
ipos.xlsx
```

The workbook contains `All IPOs`, `Open`, `Upcoming`, `Closed`, and `Listed` sheets. The export worker does not call Upstox or update PostgreSQL.
