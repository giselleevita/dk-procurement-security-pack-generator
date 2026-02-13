# Implementation Tasks (MVP)

This file is the execution checklist for a shippable MVP. Tasks are intentionally scoped to the locked feature set.

## Backend Tasks (FastAPI + Postgres)

### 1. Backend scaffold + tooling
**Description**
- Create FastAPI app with typed settings, structured logging (no secrets), and health endpoints.
- Add dependency management (pinned) and dev scripts.

**Acceptance criteria**
- `docker compose up` starts API and health check passes.
- `GET /api/health` returns 200 with `{status:"ok"}`.

**Dependencies/blockers**
- None.

### 2. Database schema + Alembic migrations
**Description**
- SQLAlchemy 2 models: users, sessions, provider_connections, evidence_runs, control_evidence.
- Alembic env/config and initial migration.

**Acceptance criteria**
- `alembic upgrade head` succeeds in container.
- Unique email enforced; all tables created.

**Dependencies/blockers**
- Task 1.

### 3. Local auth (register/login/logout) + cookie sessions
**Description**
- Email+password registration and login.
- HttpOnly cookie session; server stores only a hash of session token.

**Acceptance criteria**
- Register/login sets cookie and `GET /api/me` returns user.
- Logout invalidates session.

**Dependencies/blockers**
- Task 2.

### 4. CSRF protection for mutating endpoints
**Description**
- Issue CSRF token to frontend and require `X-CSRF-Token` header on POST/PUT/DELETE.
- Validate Origin/Referer when present.

**Acceptance criteria**
- Mutating endpoints reject missing/invalid CSRF with 403.
- Read-only endpoints remain accessible with valid session.

**Dependencies/blockers**
- Task 3.

### 5. Token crypto utilities (Fernet) + secret handling
**Description**
- Add `FERNET_KEY` required setting.
- Encrypt/decrypt provider tokens; ensure tokens never logged.

**Acceptance criteria**
- Tokens stored encrypted in DB and decrypted only in-memory.
- Logs contain no token material (manual spot-check).

**Dependencies/blockers**
- Task 2.

### 6. OAuth: GitHub connect flow
**Description**
- Implement OAuth start URL + callback code exchange.
- Store token encrypted; store scopes and provider account id.

**Acceptance criteria**
- `POST /api/connections/github/start` returns an authorize URL.
- Callback stores a valid connection row.

**Dependencies/blockers**
- Task 4, Task 5.
- Blocker: GitHub OAuth App credentials and configured redirect URI.

### 7. OAuth: Microsoft (Entra/Graph) connect flow
**Description**
- Implement OAuth start URL + callback code exchange for Microsoft identity platform v2.
- Store token encrypted; store tenant/account hints if present.

**Acceptance criteria**
- `POST /api/connections/microsoft/start` returns an authorize URL.
- Callback stores a valid connection row.

**Dependencies/blockers**
- Task 4, Task 5.
- Blocker: Entra app registration + redirect URI + admin consent for requested scopes (varies by tenant).

### 8. Connections API + forget provider
**Description**
- List connection status.
- Delete a provider connection and all its token material.

**Acceptance criteria**
- `GET /api/connections` shows connected/disconnected per provider.
- `DELETE /api/connections/{provider}` removes connection.

**Dependencies/blockers**
- Task 6, Task 7.

### 9. Evidence collection: GitHub (sample <= 10 repos)
**Description**
- GitHub collector pulls repo list (up to 10), branch protection for default branch, PR review requirements, force-push settings, admin enforcement, visibility counts.
- Store artifacts per control with computed status.

**Acceptance criteria**
- `POST /api/collect` produces GitHub control evidence rows when connected.
- If permissions missing, controls set to `unknown` with error detail stored in artifacts (not logs).

**Dependencies/blockers**
- Task 6, Task 2.

### 10. Evidence collection: Microsoft Graph
**Description**
- Graph collector pulls organization info; attempts Security Defaults and Conditional Access policy counts; attempts directory roles count heuristic.
- Store artifacts per control with computed status and `unknown` when not accessible.

**Acceptance criteria**
- `POST /api/collect` produces Microsoft control evidence rows when connected.
- Handles 403/insufficient privileges gracefully.

**Dependencies/blockers**
- Task 7, Task 2.

### 11. Pack hygiene controls (freshness/completeness/integrity/connection status)
**Description**
- Compute remaining controls from existing evidence and timestamps.

**Acceptance criteria**
- Dashboard always returns up to 12 controls including hygiene controls.

**Dependencies/blockers**
- Task 9, Task 10.

### 12. Dashboard + control detail endpoints
**Description**
- Implement `GET /api/dashboard`, `GET /api/controls`, `GET /api/controls/{key}`.

**Acceptance criteria**
- UI can render control list and detail JSON artifacts.

**Dependencies/blockers**
- Task 11.

### 13. Export pack (Markdown + PDF + Evidence ZIP)
**Description**
- Deterministic report generator (DK/EN headings).
- PDF rendered via ReportLab (simple layout).
- Evidence ZIP with `manifest.json` and artifact files (JSON) with hashes.

**Acceptance criteria**
- `POST /api/export` returns a zip download containing:
  - `report.md`
  - `report.pdf`
  - `evidence-pack.zip` (or equivalent structure)
- Manifest references match included artifacts; hashes validate.

**Dependencies/blockers**
- Task 12.

### 14. Wipe all data endpoint
**Description**
- Delete evidence + connections for current user.

**Acceptance criteria**
- `POST /api/wipe` leaves user account intact but removes provider connections and evidence.

**Dependencies/blockers**
- Task 12.

### 15. Tests (unit + integration smoke)
**Description**
- Unit tests for crypto, status evaluation, exporters.
- Integration smoke with TestClient + temporary DB (or containerized) and mocked provider calls.

**Acceptance criteria**
- `pytest` passes locally and in containers.
- Provider API calls are mocked; no network needed for tests.

**Dependencies/blockers**
- Tasks 2–14.

## Frontend Tasks (React + Vite + TypeScript)

### 1. Frontend scaffold + API client
**Description**
- Create Vite React TS app.
- Add minimal API client with cookie credentials and CSRF header support.

**Acceptance criteria**
- `web` container runs and can call `GET /api/health`.

**Dependencies/blockers**
- Backend Task 1, Backend Task 4.

### 2. Auth UI (register/login/logout)
**Description**
- Simple forms for register/login.
- Logout button in app shell.

**Acceptance criteria**
- Can register/login and see authenticated layout.
- Logout returns to login screen.

**Dependencies/blockers**
- Backend Task 3.

### 3. Connect accounts page (GitHub + Microsoft)
**Description**
- Show connection status and connect/disconnect buttons.
- OAuth starts by redirecting browser to authorize URL; callback handled by backend and frontend route.

**Acceptance criteria**
- User can connect/disconnect both providers from UI.

**Dependencies/blockers**
- Backend Tasks 6–8.
- Blockers: OAuth apps configured.

### 4. Dashboard (12 controls max)
**Description**
- Show controls with status color and last updated.
- “Collect now” button.

**Acceptance criteria**
- After collection, dashboard shows green/yellow/red/gray.

**Dependencies/blockers**
- Backend Tasks 9–12.

### 5. Control detail page
**Description**
- Control list links to detail page.
- Show deterministic notes and raw JSON artifacts (read-only).

**Acceptance criteria**
- Latest artifacts render without unsafe HTML.

**Dependencies/blockers**
- Backend Task 12.

### 6. Export UI
**Description**
- “Export pack” button triggers `/api/export` and downloads ZIP.

**Acceptance criteria**
- Downloaded file contains report.md and report.pdf and evidence zip/manifest.

**Dependencies/blockers**
- Backend Task 13.

### 7. Safety actions UI (forget provider, wipe all data)
**Description**
- Confirm dialogs for destructive actions.

**Acceptance criteria**
- Forget provider deletes connection.
- Wipe all data clears dashboard evidence and connections.

**Dependencies/blockers**
- Backend Tasks 8 and 14.

### 8. Frontend tests (smoke)
**Description**
- Basic component smoke tests (or minimal e2e-less checks) to ensure key pages render and API client wiring works.

**Acceptance criteria**
- `npm test` (or `vitest`) passes.

**Dependencies/blockers**
- Frontend Tasks 1–7.

