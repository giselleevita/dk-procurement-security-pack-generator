# Security Review (MVP) — DK Procurement Security Pack Generator

This document is written for Denmark procurement buyers and technical reviewers. It focuses on what the product does, what it stores, how it is protected, and how to delete it.

## Executive Summary
- **Deployment**: Self-hosted only via Docker Compose. No SaaS, no telemetry, no external analytics.
- **Evidence collection**: Calls GitHub API and Microsoft Graph using user-authorized OAuth tokens.
- **Storage**: Tokens are **encrypted at rest** in Postgres using Fernet (`FERNET_KEY`). Evidence is stored as JSON artifacts per control.
- **Exports**: The export pack contains **reports + evidence artifacts only**. **No tokens or secrets are included** (see “Exports”).
- **Safety**: Supports “Forget provider” and “Wipe all data”.

## System Model (Repo-Grounded)
**Frontend**
- React SPA (`frontend/`) calling backend API with `credentials: "include"` cookies (`frontend/src/api/client.ts`).

**Backend**
- FastAPI app (`backend/app/main.py`) with cookie-auth session and CSRF check (`backend/app/api/deps.py`).
- Postgres-backed persistence via SQLAlchemy (`backend/app/models/*`, `backend/app/repos/*`).
- Provider integrations:
  - GitHub OAuth/token exchange + REST API calls (`backend/app/providers/github_oauth.py`, `backend/app/providers/github_api.py`)
  - Microsoft OAuth/token exchange + Graph API calls (`backend/app/providers/microsoft_oauth.py`, `backend/app/providers/graph_api.py`)

**Exports**
- Deterministic Markdown + PDF + evidence ZIP with SHA-256 manifest (`backend/app/services/export_pack.py`, `backend/app/export/*`)

## Data Handling Statement (Local-Only)
1. The application runs locally in your environment (Docker Compose).
2. The application does not send any data to the vendor. It only communicates with:
   - GitHub APIs
   - Microsoft identity platform + Microsoft Graph APIs
3. The application does not include telemetry or external analytics.

## What Data Is Stored
All data is stored in Postgres and scoped to the local user account.

### 1) User account data
- Email (lowercased)
- Password hash (bcrypt)

### 2) Session data
- Random session token stored in **HttpOnly cookie** (browser)
- Server stores only a **hash** of the session token in DB, plus a CSRF token and expiry timestamps (`backend/app/models/session.py`)

### 3) Provider connection data
- Provider name (`github` / `microsoft`)
- Encrypted access token
- Encrypted refresh token (Microsoft only, when provided)
- Scopes, token type, expiry timestamp (Microsoft), provider account id hints (optional)

### 4) Evidence data (controls)
- Evidence runs: timestamps + overall run status
- Control evidence rows: `status` (pass/warn/fail/unknown) and `artifacts` JSON
- Artifacts include:
  - GitHub: repo names, default branch, derived branch-protection booleans, visibility counts, and limited per-repo details
  - Microsoft Graph: org display name/tenant id if accessible, Security Defaults response if accessible, Conditional Access policy count if accessible, directory roles count heuristic if accessible

## Where Data Is Stored
- Postgres volume (`pg_data`) managed by Docker Compose (`docker-compose.yml`).

## For How Long Data Is Stored
- **Indefinitely** until the user performs “Forget provider” or “Wipe all data”.
- There is no automatic retention policy in MVP.

## How To Wipe Data
### Forget provider
Action: “Forget GitHub” / “Forget Microsoft”
- Deletes stored OAuth tokens for that provider (provider connection row)
- Deterministic behavior for provider evidence is enforced in code (see validation plan)

### Wipe all data
Action: “Wipe all data”
- Deletes evidence runs and evidence rows for the current user
- Deletes provider connections and OAuth states for the current user
- Session handling on wipe is explicitly defined (see validation plan)

## Exports: What’s Included and What Is Not
### Export pack contents
`dk-security-pack.zip` contains:
- `report.md`
- `report.pdf`
- `evidence-pack.zip`

`evidence-pack.zip` contains:
- `manifest.json` with SHA-256 hashes for each included JSON artifact file
- `artifacts/<control_key>.json` per control (status/notes/artifacts)

### Explicit confirmation: No secrets included in export packs
The export generators only include:
- Control statuses
- Notes (deterministic templates)
- Evidence artifacts derived from provider API responses and derived counts

They do **not** include:
- OAuth access tokens
- OAuth refresh tokens
- OAuth client secrets
- Session cookies
- Fernet keys

This is validated by the export verification step in `VALIDATION_PLAN.md` (searches for `access_token`, `refresh_token`, `client_secret`, and `Bearer ...` patterns).

## Threat Model Review (MVP)
### Trust boundaries
1. Browser → API (cookie-authenticated HTTP)
2. API → Postgres
3. API → GitHub APIs
4. API → Microsoft identity platform + Graph
5. API → export generation (server-side filesystem/temp + download)

### Top risks and mitigations (implemented)
1. **Token theft from logs**
   - Mitigation: do not log tokens or auth codes; avoid echoing provider responses containing secrets (current code does not log tokens).
2. **CSRF on mutating endpoints**
   - Mitigation: CSRF token required via `X-CSRF-Token` header; session-bound token check in backend (`backend/app/api/deps.py`) and consistent client behavior (`frontend/src/api/client.ts`).
3. **IDOR / cross-user data access**
   - Mitigation: all DB queries are scoped by `user_id` in repository functions; endpoints use authenticated user context.
4. **XSS leading to cookie/session abuse**
   - Mitigation: UI renders artifacts as plain text (`<pre>` + `JSON.stringify`), no `dangerouslySetInnerHTML`.
5. **Export integrity issues**
   - Mitigation: evidence ZIP includes manifest with SHA-256; export validates hashes at generation time (`backend/app/services/export_pack.py`).

### Safe failure modes (required for procurement trust)
- If Graph permissions are missing, controls become `unknown` instead of crashing (collector handles 401/403).
- If tokens cannot be decrypted (key rotated/misconfigured), the system must fail safely and require reconnect (validated and enforced in fixes).

## Top 10 Failure Points (For This App Type) and Status
This section is the procurement-grade checklist of common failure modes and the current status (must be “confirmed” before release).

1. OAuth denial/error yields raw 422 or stack trace
   - Status: requires validation and (if failing) fix
2. OAuth state replay or cross-session state usage
   - Status: state stored server-side, one-time; needs denial/replay validation
3. Tokens end up in logs/exceptions
   - Status: no token logging in code; needs export/log scan validation
4. Fernet key rotation causes undefined behavior
   - Status: must fail safe (“reconnect required”) and be documented
5. CSRF is placebo (cookie auth with no real CSRF)
   - Status: CSRF header+cookie+session binding exists; origin checks must be consistent
6. Forget provider does not actually remove sensitive data
   - Status: must be deterministic (tokens removed + evidence handled)
7. Wipe all data leaves residual user data (sessions, oauth state, evidence, connections)
   - Status: must be validated and completed
8. Evidence snapshots mix across runs (inconsistent dashboard/export)
   - Status: must be fixed by ensuring each run writes a complete snapshot
9. Exports include secrets or personally sensitive values unexpectedly
   - Status: explicit “no secrets in export” validation required
10. Export manifest hashes don’t verify / integrity claim untrue
   - Status: hash verification must pass consistently

## Release Notes (Security-Relevant)
After fixes, this document must be updated to list:
- mitigations implemented
- exact wipe semantics
- exact OAuth error behavior

