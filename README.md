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

## Required Configuration (.env)
Edit `.env` and set:
- `FERNET_KEY` (generated automatically if missing)
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_OAUTH_REDIRECT_URI`
- `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT`, `MS_OAUTH_REDIRECT_URI`

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

## 3-Minute Demo Script (Click Path + What To Say)
1. **Login/Register**
   - Click: Register → create local user
   - Say: "Local-only auth using HttpOnly cookie sessions. No SaaS, no telemetry."
2. **Connect accounts**
   - Click: Connect → Connect GitHub → authorize
   - Click: Connect Microsoft → authorize
   - Say: "Tokens are stored encrypted at rest; we never log tokens; 'Forget' deletes tokens."
3. **Collect evidence**
   - Click: Dashboard → Collect now
   - Say: "We pull deterministic evidence from GitHub and Microsoft Graph and store artifacts per control."
4. **Show controls**
   - Click: any control row → view Notes + raw JSON artifacts
   - Say: "The narrative is deterministic and directly derived from evidence; raw artifacts are visible."
5. **Export pack**
   - Click: Export pack (ZIP)
   - Say: "Export includes report.md, a simple report.pdf, and an evidence-pack.zip with manifest + hashes."
6. **Safety**
   - Click: Connect → Wipe all data (confirm)
   - Say: "One-click safety actions: forget provider, wipe all evidence and connections for the user."

## Notes
- Evidence is computed from current provider permissions. If Graph endpoints are not accessible, the control becomes `unknown` (not a crash).
- GitHub evidence samples up to 10 repositories per run (most recently updated).

