#!/bin/bash
set -e

echo "=== PEARL Backend Startup ==="
echo "Running database migrations..."

# Get current alembic version (if any)
CURRENT_VERSION=$(alembic current 2>&1 | grep -o '[a-f0-9]\{12\}' | head -1 || echo "")

if [ -n "$CURRENT_VERSION" ]; then
    echo "Found alembic version: $CURRENT_VERSION"
    echo "Running upgrade to apply any new migrations..."
    alembic upgrade head
else
    echo "No alembic version found in database."
    
    # Try a normal upgrade first - this works for fresh databases
    echo "Attempting migration upgrade..."
    if alembic upgrade head 2>&1; then
        echo "Migrations applied successfully."
    else
        # If upgrade fails (tables exist), stamp and retry
        echo "Migration failed - tables may already exist."
        echo "Stamping database with current head..."
        alembic stamp head
        echo "Database stamped. Running upgrade again..."
        alembic upgrade head
    fi
fi

echo "Migrations complete."
echo "=== Starting PEARL Backend ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
