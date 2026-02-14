#!/usr/bin/env sh
set -eu

# Canonical entrypoint for local dev.
exec "$(cd "$(dirname "$0")" && pwd)/scripts/dev-up.sh" "$@"

