#!/usr/bin/env sh
set -eu

cd /app

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running migrations..."
  alembic -c alembic.ini upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

