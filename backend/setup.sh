#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "========================================"
echo "        AUGUR BACKEND SETUP"
echo "========================================"

# --------------------------------------------------
# 1. Check required system commands
# --------------------------------------------------

echo
echo "[1/7] Checking system dependencies..."

for cmd in python3 psql pg_isready; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: '$cmd' is not installed."
        exit 1
    fi
done

echo "System dependencies: OK"


# --------------------------------------------------
# 2. Create Python virtual environment
# --------------------------------------------------

echo
echo "[2/7] Setting up Python virtual environment..."

if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    echo "Created .venv"
else
    echo ".venv already exists"
fi

source .venv/bin/activate

python -m pip install --upgrade pip


# --------------------------------------------------
# 3. Install Python dependencies
# --------------------------------------------------

echo
echo "[3/7] Installing Python dependencies..."

pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "Python dependencies: OK"


# --------------------------------------------------
# 4. Check .env
# --------------------------------------------------

echo
echo "[4/7] Checking environment configuration..."

if [[ ! -f ".env" ]]; then
    echo "ERROR: .env not found."
    echo
    echo "Create it from:"
    echo "    cp .env.example .env"
    echo
    echo "Then configure DB_* and UPSTOX_ACCESS_TOKEN."
    exit 1
fi

# Export .env variables for this script.
set -a
source .env
set +a

required_vars=(
    DB_HOST
    DB_PORT
    DB_NAME
    DB_USER
    DB_PASSWORD
    UPSTOX_ACCESS_TOKEN
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        echo "ERROR: $var is not set in .env"
        exit 1
    fi
done

echo "Environment configuration: OK"


# --------------------------------------------------
# 5. Check PostgreSQL
# --------------------------------------------------

echo
echo "[5/7] Checking PostgreSQL..."

if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
    echo "PostgreSQL is not reachable at $DB_HOST:$DB_PORT"

    echo "Trying to start PostgreSQL..."

    sudo systemctl start postgresql

    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
        echo "ERROR: PostgreSQL is still unreachable."
        exit 1
    fi
fi

echo "PostgreSQL: OK"


# --------------------------------------------------
# 6. Create PostgreSQL user + database
# --------------------------------------------------

echo
echo "[6/7] Configuring PostgreSQL database..."

sudo -u postgres psql \
    -v ON_ERROR_STOP=1 \
    -v db_user="$DB_USER" \
    -v db_password="$DB_PASSWORD" \
    -v db_name="$DB_NAME" \
    -d postgres <<'SQL'

SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L',
    :'db_user',
    :'db_password'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = :'db_user'
)\gexec

ALTER ROLE :"db_user"
WITH LOGIN PASSWORD :'db_password';

SELECT format(
    'CREATE DATABASE %I OWNER %I',
    :'db_name',
    :'db_user'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = :'db_name'
)\gexec

ALTER DATABASE :"db_name"
OWNER TO :"db_user";

SQL

echo "PostgreSQL database: OK"


# --------------------------------------------------
# 7. Run Alembic migrations
# --------------------------------------------------

echo
echo "[7/7] Applying database migrations..."

alembic upgrade head

echo "Database schema: OK"


echo
echo "========================================"
echo "         AUGUR SETUP COMPLETE"
echo "========================================"

echo
echo "Database:"
echo "  $DB_NAME"

echo
echo "User:"
echo "  $DB_USER"

echo
echo "Python:"
echo "  $(python --version)"

echo
echo "Run:"
echo "  source .venv/bin/activate"

echo
echo "Start:"
echo "  python sync.py"