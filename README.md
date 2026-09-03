# DK Procurement Security Pack Generator

**Status: public synthetic-data demo candidate · v1.0 security-pack format**

Turns normalized evidence into a procurement report, evidence archive, and independently verifiable Ed25519-signed manifest. See the [engineering case study](docs/engineering-case-study.md) for architecture, trust boundaries, limitations, and a five-minute review path.

**Self-hosted evidence collection and security-pack generation for procurement reviews.**

The application collects authorized Microsoft 365 and GitHub evidence, maps it to a
12-control review snapshot, and exports a signed documentation pack containing Markdown,
PDF, and machine-readable evidence artifacts.

This is a reference implementation. Validate its controls, deployment configuration, and
generated statements independently before using them in a real procurement process.

## Engineering Highlights

- Local FastAPI, React, and PostgreSQL stack
- Encrypted OAuth-token storage and explicit provider/data deletion controls
- Offline deterministic demo mode
- Ed25519-signed export manifests with SHA-256 artifact hashes
- Strict offline verification rejects incomplete manifests, unexpected files, unsafe paths, duplicates, and archive bombs
- Host, origin, cookie, and CSRF hardening controls
- Backend tests and API container build enforced in CI

## One-Command Local Run
```sh
./dev-up.sh
```

## Demo Mode (Offline)
For a demo that does not require GitHub/Microsoft OAuth, start with `APP_ENV=demo` and seed a deterministic demo user + evidence snapshot:

```sh
# Start containers
./dev-up.sh -d

# Seed a local demo user + 12-control snapshot with your own throwaway password
docker compose exec api python -m app.scripts.seed_demo --password "replace-with-a-local-password"

# Login with demo@example.com and that local password
```


Canonical run script: `./dev-up.sh`.

This will:
- create `.env` from `.env.example` if missing (including a generated `FERNET_KEY`)
- start Postgres, FastAPI API, and the React dev server via Docker Compose

Open:
- Web UI: `http://localhost:5173`
- API health: `http://localhost:8000/api/health`

First-time use: click **Register** in the UI and create a local account (email must be a valid format, e.g. `demo@example.com`).


## Data Handling Statement
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

For the Render blueprint, supply `FERNET_KEY` as a secret generated with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
The blueprint deliberately does not commit or invent this credential.

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
