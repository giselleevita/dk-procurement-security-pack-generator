#!/usr/bin/env sh
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env" ]; then
  if [ ! -f ".env.example" ]; then
    echo "Missing .env.example" >&2
    exit 1
  fi

  echo "Creating .env from .env.example"
  cp .env.example .env

  if command -v python3 >/dev/null 2>&1; then
    # Fernet key format: urlsafe base64-encoded 32 random bytes.
    FERNET_KEY="$(python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")"
    # macOS/BSD sed needs -i '' for in-place edits.
    sed -i '' "s/^FERNET_KEY=REPLACE_ME$/FERNET_KEY=${FERNET_KEY}/" .env || true
  else
    echo "python3 not found; please set FERNET_KEY in .env" >&2
  fi
fi

docker compose up --build
