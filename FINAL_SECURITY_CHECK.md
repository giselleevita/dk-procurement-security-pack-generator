# Final Pre-Ship Security Sanity Check

Scope: last-pass review for procurement-facing security footguns (logging, cookies, CORS/origin, export ZIP safety, auth/CSRF, error leakage). Minimal/no-code-change intent.

## Verified

- Sensitive query parameters are not logged.
  - Uvicorn access logs are disabled in `backend/entrypoint.sh` (`--no-access-log`) to avoid leaking OAuth callback query strings like `?code=...`.
  - Repo search found no application logging of `request.url`, `request.query_params`, or similar request URL dumps.
  - OAuth callback handlers in `backend/app/api/routes/oauth.py` do not log or echo `code`/`state` values.

- Session cookies are configured for browser safety.
  - Session cookie `dkpack_session`: `HttpOnly=true`, `SameSite=Lax`, `Secure` controlled by `COOKIE_SECURE`, `Max-Age` aligned to server-side session expiry (`backend/app/core/cookies.py`, `backend/app/api/routes/auth.py`).
  - CSRF cookie `dkpack_csrf`: `HttpOnly=false` (by design for SPA header echo), `SameSite=Lax`, `Secure` controlled by `COOKIE_SECURE`, `Max-Age` aligned to session expiry (`backend/app/core/cookies.py`, `backend/app/api/routes/auth.py`).

- CORS/origin hardening is enforced (without breaking local tooling).
  - CORS middleware allowlist comes from `ALLOWED_ORIGINS` and rejects wildcard `*` (`backend/app/core/settings.py`, `backend/app/main.py`).
  - Mutating endpoints enforce CSRF and (when present) validate the `Origin` header against `ALLOWED_ORIGINS` (`backend/app/api/deps.py`).
  - When `Origin` is missing, requests are permitted to avoid breaking `curl`/local tooling; protection relies on `SameSite=Lax` cookies plus CSRF header requirements for browser-based state changes.

- Export ZIP path traversal (ZIP slip) is prevented.
  - Inner evidence ZIP uses fixed `manifest.json` and writes artifact filenames derived from control keys with traversal characters removed (`backend/app/export/evidence_zip.py`).
  - Outer pack ZIP writes only fixed filenames: `report.md`, `report.pdf`, `evidence-pack.zip` (`backend/app/services/export_pack.py`).

- “Forget provider” / “Wipe all data” require auth + CSRF.
  - Forget provider: `DELETE /api/connections/{provider}` uses `get_auth_ctx` + `require_csrf` (`backend/app/api/routes/connections.py`).
  - Wipe all data: `POST /api/wipe` uses `get_auth_ctx` + `require_csrf` and clears cookies (`backend/app/api/routes/wipe.py`).

- Error responses do not leak stack traces in production mode.
  - FastAPI is created without debug mode; Swagger/OpenAPI endpoints are disabled unless `APP_ENV=dev` (`backend/app/main.py`).
  - OAuth failures return user-readable redirects without stack traces (`backend/app/api/routes/oauth.py`).

## Fixes Made In This Pass

- None required based on the checks above.

## Remaining Accepted Risks / Deployment Notes

- Reverse proxies: ensure query strings are not logged (OAuth callbacks include `code` in the URL). Even though the app disables Uvicorn access logs, upstream proxies can still log request URLs.
- If `COOKIE_SECURE=false` and the app is reachable over a non-local network, cookies could traverse HTTP. For demo/procurement use behind TLS, set `COOKIE_SECURE=true`.
- Origin enforcement is conditional on the `Origin` header being present. This is intentional to keep local tooling working, and mutating endpoints still require CSRF; for stricter deployments, consider requiring `Origin` for browser-facing requests only.

## Commands Run

```sh
python3 -m compileall -q backend/app backend/tests
```

