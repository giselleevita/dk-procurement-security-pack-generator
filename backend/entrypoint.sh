#!/usr/bin/env sh
set -eu

cd /app

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running migrations..."
  alembic -c alembic.ini upgrade head
fi

if [ "${APP_ENV:-dev}" = "dev" ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --no-access-log
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
fi
