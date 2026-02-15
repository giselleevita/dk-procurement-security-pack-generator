# DK Procurement Security Pack Generator (Self-hosted MVP)

Generate Danish procurement-ready security documentation locally (no SaaS) from Microsoft 365 (Graph) + GitHub evidence.

Disclaimer: demo-grade MVP. Do not use in production without independent security review.

## 1-Command Local Run
```sh
./dev-up.sh
```

## Demo mode (offline)
For a demo that does not require GitHub/Microsoft OAuth, start with `APP_ENV=demo` and seed a deterministic demo user + evidence snapshot:

```sh
# Start containers
./dev-up.sh -d

# Seed demo user + 12-control snapshot
docker compose exec api python -m app.scripts.seed_demo

# Login in the UI
# email: demo@example.com
# password: password123
```


Canonical run script: `./dev-up.sh`.

This will:
- create `.env` from `.env.example` if missing (including a generated `FERNET_KEY`)
- start Postgres, FastAPI API, and the React dev server via Docker Compose

Open:
- Web UI: `http://localhost:5173`
- API health: `http://localhost:8000/api/health`

First-time use: click **Register** in the UI and create a local account (email must be a valid format, e.g. `demo@example.com`).


## Data Handling Statement (Procurement-Friendly)
- Self-hosted and local-only: runs in your environment via Docker Compose.
- No SaaS, no telemetry, no external analytics.
- OAuth tokens are stored **encrypted at rest** in Postgres using Fernet (`FERNET_KEY`).
- If `FERNET_KEY` is rotated/changed, existing tokens can no longer be decrypted; users must **reconnect providers**.
- Evidence is collected only when you click **Collect now**.
- Export packs are procurement evidence packs and contain reports and evidence artifacts only:
  - **No OAuth tokens**
  - **No OAuth client secrets**
  - **No encryption keys**
- Optional: local action audit log is recorded in the database (no tokens, no OAuth codes); cleared by "Wipe all data".
- Safety actions:
  - **Forget provider** deletes provider tokens and clears that provider’s evidence.
  - **Wipe all data** deletes evidence + connections + oauth states + sessions and logs the user out.

## Evidence integrity (signed packs)
- Each downloaded `dk-security-pack.zip` includes `pack_manifest.json` (SHA-256 hashes for `report.md`, `report.pdf`, `evidence-pack.zip`) and `pack_manifest.sig` (signature).
- Signing mode: Ed25519 (preferred) using a local instance key stored under `backend/app/state/` (gitignored).
- This is tamper-evident: changes to the pack payload files are detected by hash mismatch and/or signature failure.
- Limitation: the trust anchor is the local instance key; if the instance is reinstalled or the key is rotated, old packs may not verify against the new instance key.

## Export Naming and Structure
- Download name: `dk-security-pack.zip`
- Contents:
  - `report.md`
  - `report.pdf`
  - `evidence-pack.zip` (contains `manifest.json` and `artifacts/*.json`)

## Required Configuration (.env)
Edit `.env` and set:
- `FERNET_KEY` (generated automatically if missing)
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_OAUTH_REDIRECT_URI`
- `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT`, `MS_OAUTH_REDIRECT_URI`
- Optional: `ALLOWED_ORIGINS` (comma-separated) for CORS/CSRF origin checks
- Optional: `ALLOWED_HOSTS` (comma-separated) for Host header validation (TrustedHostMiddleware)
- Production hardening: set `COOKIE_SECURE=true` when running behind HTTPS/TLS

### OAuth Redirect URIs
GitHub OAuth App:
- `http://localhost:8000/api/oauth/github/callback`

Microsoft Entra App Registration:
- `http://localhost:8000/api/oauth/microsoft/callback`

After completing OAuth in the browser you are redirected back to the UI:
- `/connections?provider=github&status=connected`
- `/connections?provider=microsoft&status=error&error=...`

## Common Commands
Migrations (runs automatically on API container start):
```sh
docker compose exec api alembic -c alembic.ini upgrade head
```

Backend tests:
```sh
docker compose exec api pytest
```

Frontend:
```sh
docker compose exec web npm run lint
```

## Demo
See `DEMO_SCRIPT.md`.

## Notes
- Evidence is computed from current provider permissions. If Graph endpoints are not accessible, the control becomes `unknown` (not a crash).
- GitHub evidence samples up to 10 repositories per run (most recently updated).
