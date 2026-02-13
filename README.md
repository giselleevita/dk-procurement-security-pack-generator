# DK Procurement Security Pack Generator (Self-hosted MVP)

Generate Danish procurement-ready security documentation locally (no SaaS) from Microsoft 365 (Graph) + GitHub evidence.

## 1-Command Local Run
```sh
./scripts/dev-up.sh
```

This will:
- create `.env` from `.env.example` if missing (including a generated `FERNET_KEY`)
- start Postgres, FastAPI API, and the React dev server via Docker Compose

Open:
- Web UI: `http://localhost:5173`
- API health: `http://localhost:8000/api/health`

## Data Handling Statement (Procurement-Friendly)
- Self-hosted and local-only: runs in your environment via Docker Compose.
- No SaaS, no telemetry, no external analytics.
- OAuth tokens are stored **encrypted at rest** in Postgres using Fernet (`FERNET_KEY`).
- If `FERNET_KEY` is rotated/changed, existing tokens can no longer be decrypted; users must **reconnect providers**.
- Evidence is collected only when you click **Collect now**.
- Export packs contain reports and evidence artifacts only:
  - **No OAuth tokens**
  - **No OAuth client secrets**
  - **No encryption keys**
- Safety actions:
  - **Forget provider** deletes provider tokens and clears that provider’s evidence.
  - **Wipe all data** deletes evidence + connections and logs the user out.

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
