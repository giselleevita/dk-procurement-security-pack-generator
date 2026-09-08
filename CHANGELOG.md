# Changelog

## 1.2.0 - 2026-09-08

- Add a one-click synthetic golden path that collects, signs, independently verifies, and safely demonstrates tamper rejection.
- Add a recruiter-facing integrity proof panel with signer and artifact fingerprints.
- Strengthen the free-demo cold-start and synthetic-data notice.
- Make the migration chain portable across production PostgreSQL and disposable SQLite demos.

## 1.1.1 - 2026-09-03

- Require the signed manifest to enumerate exactly every security-pack payload.
- Reject duplicate, unexpected, unsafe, oversized, and decompression-heavy ZIP structures before verification.
- Add adversarial verifier-boundary regression tests.

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
