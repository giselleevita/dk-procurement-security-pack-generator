# Release Candidate Status (RC)

This repository contains a self-hosted, local-only MVP for the **DK Procurement Security Pack Generator**: a tool that connects to **GitHub** and **Microsoft 365 (Entra/Graph)**, collects evidence, evaluates **12 procurement-friendly controls**, and exports a procurement-ready vendor documentation evidence pack (`dk-security-pack.zip`) containing `report.md`, `report.pdf`, and `evidence-pack.zip` (with `manifest.json` + `artifacts/*.json` and SHA-256 hashes).

## Trust Posture
- **Local-only, no telemetry**: runs in your environment (Docker Compose). No SaaS, no external analytics.
- **Token encryption at rest (Fernet)**: OAuth access/refresh tokens are stored encrypted in Postgres using `FERNET_KEY`. If `FERNET_KEY` changes, stored tokens cannot be decrypted and **reconnect is required**.
- **Origin/host hardening**:
  - CSRF: HttpOnly cookie sessions + CSRF token header (`X-CSRF-Token`) bound to the session.
  - Origin allowlist: mutating requests with `Origin` must match `ALLOWED_ORIGINS`.
  - Host allowlist: TrustedHostMiddleware uses `ALLOWED_HOSTS`.
  - Baseline headers: `nosniff`, `no-referrer`, `DENY` are set by the backend.
- **No access log leakage**: Uvicorn access logs are disabled (`--no-access-log`) to avoid logging OAuth callback query strings containing `?code=...`.
- **Deterministic deletion semantics**:
  - **Forget provider** deletes provider connection (tokens) and provider evidence (provider controls become `unknown`).
  - **Wipe all data** deletes evidence + connections + oauth states + sessions, clears cookies, and logs the user out.
- **No secrets in export packs (guarantee + tests)**:
  - Export generation includes evidence artifacts and deterministic notes only (no tokens/secrets/keys).
  - Backend tests assert exported **text** files contain no secret markers and no JWT-like token patterns, and avoid scanning PDFs to prevent false positives.
  - The validation plan includes hash verification and a “no secrets” scan for exported zips.

## Demo Flow (Max 10 Steps)
1. Start the stack: `./dev-up.sh`
2. Open the UI: `http://localhost:5173`
3. Register or login (local email/password; HttpOnly cookie session).
4. Go to **Connect** and connect **GitHub** (OAuth).
5. Connect **Microsoft (Entra/Graph)** (OAuth); if consent/permissions are missing, the UI shows a readable error and evidence becomes `unknown` instead of crashing.
6. Go to **Dashboard** and click **Collect now** (can run twice; stays deterministic and always returns 12 controls).
7. Click a control to view deterministic notes and raw JSON artifacts.
8. Click **Export pack (ZIP)**; download `dk-security-pack.zip`.
9. (Optional) Verify manifest hashes and “no secrets” scan per `VALIDATION_PLAN.md`.
10. Use safety actions: **Forget provider** and/or **Wipe all data** (verify logout on wipe).

## Validation Commands
```sh
./dev-up.sh
docker compose exec api pytest
cd frontend && npm run build
```
Then follow: `VALIDATION_PLAN.md`

## Known Limitations (Honest, Max 8)
- Microsoft Graph evidence depends on tenant configuration and admin consent; some endpoints may return 401/403 and will be reported as `unknown`.
- Conditional Access and directory role evidence may be unavailable without elevated read scopes; the MVP degrades gracefully rather than failing the pack.
- GitHub evidence sampling is limited (up to 10 repos per run) to keep the MVP fast and rate-limit friendly.
- Export PDF rendering is intentionally simple (ReportLab) and not a pixel-perfect tender template.
- Key rotation for `FERNET_KEY` is not automated; changing it requires reconnecting providers.
- Self-hosted only (Docker Compose). No hosted/SaaS mode.
- No background scheduling; evidence collection is manual (“Collect now”).
- Evidence is deterministic and evidence-backed only; there is no AI/LLM narrative generation.

## File Map (Read These First)
- `SPEC.md`
- `DESIGN.md`
- `README.md`
- `VALIDATION_PLAN.md`
- `SECURITY_REVIEW.md`
- `DEMO_SCRIPT.md`
