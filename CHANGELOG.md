# Changelog

## 1.1.0 — 2026-09-03

- Added RFC 7636 S256 PKCE to GitHub and Microsoft OAuth authorization flows.
- Store short-lived PKCE verifiers encrypted and invalidate legacy non-PKCE states during migration.
- Added an integration assertion that independently reconstructs the authorization challenge.

## 1.0.0 — 2026-09-03

- Added versioned signed-pack manifests and offline/API verification.
- Added disposable passwordless synthetic demo sessions.
- Added bounded CSV/ZIP handling and stronger browser security headers.
- Added a single-container public demo and Render blueprint.
- Updated Python and frontend dependencies and added security gates.
