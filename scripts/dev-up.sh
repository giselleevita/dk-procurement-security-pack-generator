#!/usr/bin/env sh
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Make local dev "just work" on macOS where Docker Desktop's CLI may not be on PATH.
DOCKER_BIN="docker"
if ! command -v "$DOCKER_BIN" >/dev/null 2>&1; then
  if [ -x "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
    DOCKER_BIN="/Applications/Docker.app/Contents/Resources/bin/docker"
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
  else
    echo "docker not found on PATH, and Docker Desktop CLI not found at /Applications/Docker.app/Contents/Resources/bin/docker" >&2
    echo "Install Docker (or start Docker Desktop) and try again." >&2
    exit 1
  fi
fi

# If Docker is configured to use Docker Desktop's credential helper, ensure it's discoverable.
if ! command -v docker-credential-desktop >/dev/null 2>&1; then
  if [ -x "/Applications/Docker.app/Contents/Resources/bin/docker-credential-desktop" ]; then
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
  fi
fi

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

"$DOCKER_BIN" compose up --build "$@"
