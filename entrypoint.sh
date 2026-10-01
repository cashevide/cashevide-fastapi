#!/bin/sh
set -e

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.1
done

echo "PostgreSQL started!"

echo "Running migrations..."
/app/.venv/bin/alembic upgrade head

exec "$@"
