#!/bin/bash
set -e

echo "=== PEARL Backend Startup ==="

# Function to check if alembic_version table has entries
has_alembic_version() {
    alembic current 2>&1 | grep -q '[a-f0-9]\{8,}'
    return $?
}

echo "Checking database migration status..."

if has_alembic_version; then
    CURRENT=$(alembic current 2>&1 | grep -o '[a-f0-9]\{8,}' | head -1)
    echo "Current alembic version: $CURRENT"
    echo "Applying any pending migrations..."
    alembic upgrade head
else
    echo "No alembic version found."
    echo "Attempting fresh migration..."
    
    # Try upgrade - works for new databases or databases with tables
    if alembic upgrade head 2>&1; then
        echo "Migration successful."
    else
        echo "Upgrade failed. Stamping database and retrying..."
        # If tables exist but tracking doesn't, stamp then upgrade
        alembic stamp head
        alembic upgrade head
    fi
fi

echo "Database migrations complete."
echo ""
echo "=== Starting PEARL Backend ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
