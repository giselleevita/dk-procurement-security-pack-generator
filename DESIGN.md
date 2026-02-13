# DK Procurement Security Pack Generator — Technical Design (MVP)

This design targets a self-hosted, local-only deployment. The product runs entirely in the user’s environment and does not send data to external services beyond calling Microsoft Graph and GitHub APIs for the user-authorized evidence collection.

## Architecture (Clean, Shippable MVP)
**Components**
- **Frontend**: React + Vite + TypeScript SPA
- **Backend API**: FastAPI (Python)
- **Database**: Postgres
- **Exporters**: Markdown generator + PDF renderer (ReportLab) + Evidence ZIP builder
- **Provider clients**:
  - GitHub API client (REST)
  - Microsoft Graph client (REST)

**Layering (Backend)**
- `api/` (FastAPI routers): request/response validation, auth dependency, error shaping
- `services/`: business logic (collectors, evidence evaluation, exports)
- `providers/`: GitHub/Graph HTTP clients + OAuth token exchange/refresh
- `repos/`: DB access layer (SQLAlchemy queries)
- `models/`: SQLAlchemy ORM models
- `crypto/`: token encryption/decryption utilities (Fernet)
- `export/`: markdown/pdf/zip generation

**Data flow**
1. User logs in → session cookie created (HttpOnly)
2. User connects GitHub/Microsoft → OAuth code exchanged → token encrypted and stored
3. User triggers “Collect now” → backend calls providers → stores artifacts per control → computes status
4. UI reads dashboard/control details from backend
5. Export pack → backend builds `report.md`, `report.pdf`, and `evidence-pack.zip` with `manifest.json`

## Deployment Model (Local-only)
- Docker Compose runs:
  - `api` (FastAPI)
  - `db` (Postgres)
  - `web` (Vite dev server for dev; for “shippable”, a production build can be served by the API container or nginx later)
- No telemetry, no external analytics.
- Secrets supplied via environment variables / `.env` (not committed).

## Data Model (Postgres)
All rows are scoped to a `user_id`.

**users**
- `id` (uuid, pk)
- `email` (citext or lowercased unique)
- `password_hash` (bcrypt/argon2 hash)
- `created_at`

**sessions**
- `id` (uuid, pk)
- `user_id` (fk)
- `token_hash` (hash of random session token; raw token never stored)
- `created_at`, `expires_at`, `revoked_at` (nullable)
- `last_seen_at`

**provider_connections**
- `id` (uuid, pk)
- `user_id` (fk)
- `provider` (enum: `github`, `microsoft`)
- `encrypted_access_token` (bytea/text)
- `encrypted_refresh_token` (nullable)
- `scopes` (text)
- `token_type` (text)
- `expires_at` (nullable)
- `provider_account_id` (nullable; e.g., GitHub user id, tenant id)
- `created_at`, `updated_at`

**evidence_runs**
- `id` (uuid, pk)
- `user_id` (fk)
- `started_at`, `finished_at`
- `status` (enum: `success`, `partial`, `failed`)
- `error_summary` (nullable)

**control_evidence**
- `id` (uuid, pk)
- `user_id` (fk)
- `run_id` (fk evidence_runs)
- `control_key` (text, indexed)
- `provider` (nullable: `github`/`microsoft`/`pack`)
- `status` (enum: `pass`, `warn`, `fail`, `unknown`)
- `artifacts` (jsonb): structured evidence payload (provider responses, derived counts)
- `notes` (text): deterministic explanation template output
- `collected_at`

## Controls and Evidence Semantics
- Each control stores the **latest** computed status and its underlying artifacts as JSON.
- Collector runs store per-run rows; dashboard uses latest row per `control_key`.
- “Unknown” is valid when Graph/GitHub permissions are insufficient or endpoints are unavailable.

## API Endpoints (MVP)
All endpoints are relative to `/api`.

**Auth**
- `POST /auth/register` `{email, password}` → sets session cookie
- `POST /auth/login` `{email, password}` → sets session cookie
- `POST /auth/logout` → clears session cookie / revokes session
- `GET /me` → current user profile

**OAuth + Connections**
- `POST /oauth/github/start` → returns OAuth authorize URL (with `state`)
- `GET /oauth/github/callback?code=...&state=...` → exchanges code and stores encrypted token; redirects back to web UI
- `POST /oauth/microsoft/start` → returns OAuth authorize URL (with `state`)
- `GET /oauth/microsoft/callback?code=...&state=...` → exchanges code and stores encrypted token; redirects back to web UI
- `GET /connections` → list provider connection status (connected/scopes/updated_at)
- `DELETE /connections/{provider}` → “Forget provider”

**Evidence collection**
- `POST /collect` → triggers collection now; returns run id + summary
- `GET /dashboard` → list 12 controls with latest status + timestamps
- `GET /controls` → list controls (metadata + latest status)
- `GET /controls/{control_key}` → latest artifacts + notes + timestamps

**Exports**
- `POST /export` → returns a downloadable ZIP containing report.md, report.pdf, evidence-pack.zip (or one combined zip)

**Safety**
- `POST /wipe` → deletes evidence + connections for current user

## Auth Model (Local Users + Cookie Sessions)
- Session is a random token stored in an **HttpOnly** cookie.
- Backend stores only a hash of the session token (to limit damage if DB leaks).
- Cookie settings:
  - `HttpOnly=true`
  - `Secure=true` in production (configurable for local dev)
  - `SameSite=Lax` (or `Strict` if feasible)
  - Short-ish session TTL with sliding refresh on activity (MVP: fixed TTL is acceptable).

**CSRF**
- Because auth uses cookies, implement CSRF protection for state-changing requests:
  - Issue a CSRF token (non-HttpOnly) and require `X-CSRF-Token` header on mutating endpoints.
  - Validate `Origin`/`Referer` in addition when present.

## OAuth Integrations (GitHub + Microsoft)
MVP uses OAuth Authorization Code flow.

**General token handling rules**
- Never log tokens or authorization codes.
- Encrypt tokens at rest using Fernet key from `FERNET_KEY`.
- On each provider API call:
  - Decrypt access token in-memory
  - If expired and refresh token exists, refresh and update stored token (where applicable)

### GitHub OAuth (OAuth App)
- Scopes (minimal practical for MVP):
  - `repo` (to read branch protection on private repos)
  - `read:org` (if org membership needed for repo listing)
  - `read:user`
- Evidence collected (up to 10 repos):
  - Repos list (owned + accessible)
  - Default branch name
  - Branch protection settings for default branch:
    - required PR reviews
    - force push allowance
    - enforce admins
  - Visibility counts: public/private/internal (warn if any public)

### Microsoft Entra / Graph OAuth
- Permissions vary by tenant and admin consent. MVP must handle “not authorized” gracefully and mark controls `unknown`.
- Preferred scopes (subject to feasibility):
  - `openid profile email offline_access`
  - `Organization.Read.All`
  - `Policy.Read.All` (Security Defaults + Conditional Access list)
  - (Optional/if needed for directory roles heuristic) `Directory.Read.All` or more specific role management read scope.

Evidence collected:
- Organization info (tenant display name, verified domains if accessible)
- Security Defaults policy status (if accessible)
- Conditional Access policy count (if accessible)
- Directory roles count (heuristic, if accessible)

## Export Pack Format
Exports are derived from stored evidence, not live provider calls.

**Report**
- `report.md`: bilingual DK/EN headings per control, status, timestamp, deterministic notes, and a short “Evidence summary” table.
- `report.pdf`: simple render (headings + paragraphs + tables as plain text acceptable for MVP).

**Evidence ZIP**
- `manifest.json` includes:
  - generation timestamp
  - app version
  - user id (or anonymized identifier)
  - list of controls with:
    - status
    - collected_at
    - artifact filenames and SHA-256 hashes
- Artifacts saved as JSON files (one per control/run or latest only for MVP).

## Threat Model (MVP)
This threat model is specific to the MVP described here (FastAPI + Postgres + SPA, local self-hosted).

### Trust Boundaries
1. Browser (user) → Backend API (cookie-authenticated HTTP)
2. Backend API → Postgres (SQL connection)
3. Backend API → GitHub API (HTTPS with OAuth token)
4. Backend API → Microsoft Graph (HTTPS with OAuth token)
5. Backend API → Export generation (filesystem temp + streaming download)

### Assets
- User credentials (password hashes)
- Session tokens (cookie; server-side hash)
- Provider access/refresh tokens (encrypted at rest; decrypted in memory)
- Evidence artifacts (may include org metadata, repo names, security config)
- Export bundles (report + evidence zip)
- Fernet key (`FERNET_KEY`) and OAuth client secrets

### Attacker Capabilities (Realistic)
- Remote attacker on same network can attempt web attacks if service is bound to non-loopback.
- Malicious website can attempt CSRF if user is logged in.
- Malicious local user on host can read env files if misconfigured.
- Authenticated user can attempt to access/modify other users’ evidence (IDOR).
- Provider API rate-limits or partial permissions can cause degraded collection (integrity/availability).

### Key Abuse Paths (Prioritized)
1. **Token theft via logs or exports**
   - Impact: provider account compromise.
   - Mitigations: never log tokens/codes; sanitize errors; ensure exports never include tokens; encrypt tokens at rest.

2. **CSRF on mutating endpoints (`/collect`, `/export`, `/wipe`, `/connections/*`)**
   - Impact: unwanted data wipe, forced collection, forced provider disconnect.
   - Mitigations: CSRF token + Origin/Referer checks; SameSite cookie; confirm-destructive actions in UI.

3. **IDOR / authorization bugs (cross-user access)**
   - Impact: evidence leakage and tampering.
   - Mitigations: enforce `user_id` scoping in every query; avoid exposing raw IDs in URLs when unnecessary.

4. **XSS leading to account takeover**
   - Impact: session abuse, data exfil via authenticated calls.
   - Mitigations: strict output encoding; no unsafe HTML rendering of artifacts; Content Security Policy (MVP: basic CSP headers).

5. **SQL injection / query abuse**
   - Impact: DB compromise.
   - Mitigations: SQLAlchemy parameterization; input validation; avoid raw SQL.

6. **Export path traversal / unsafe file handling**
   - Impact: writing/reading unintended files, leaking secrets into export.
   - Mitigations: generate artifacts with server-generated filenames only; never accept user-provided file paths; write to temp dir.

7. **SSRF via provider URLs**
   - Impact: internal network reachability.
   - Mitigations: hardcode provider base URLs; disallow arbitrary URLs.

### Assumptions (Influence Risk)
- The deployment is on a trusted host and not publicly exposed to the internet.
- TLS termination may be handled externally for “real” deployments; local dev may run HTTP.
- Users do not share the same OS account on the host (otherwise local file access dominates).

### Open Questions (Optional to Confirm Later)
- Will the service bind to `127.0.0.1` only by default, or to `0.0.0.0` for LAN access?
- Is this intended for single-user use, or do we expect multiple local accounts routinely?
- Do we require HTTPS in the default Compose stack (Caddy/Traefik), or document it as a production hardening step?

## Key Design Decisions (Resolved for MVP)
- Evidence is stored as JSON artifacts per control; narrative is deterministic templates only.
- Provider permission gaps yield `unknown` rather than failing the whole pack.
- Max 10 GitHub repos sampled per collection run (speed + rate limits).
- Token encryption uses Fernet with a single key (rotation documented as future work).
