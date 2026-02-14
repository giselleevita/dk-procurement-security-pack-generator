# FINAL_SUMMARY

## RC artifacts present
List:
- SPEC.md
- DESIGN.md
- IMPLEMENTATION_TASKS.md
- VALIDATION_PLAN.md
- SECURITY_REVIEW.md
- DEMO_SCRIPT.md
- RC_STATUS.md
- FINAL_SECURITY_CHECK.md

## What changed since initial MVP
Brief bullets:
- OAuth hardening (safe redirects, one-time state, no URL/query logging)
- Deterministic evidence snapshots (12 controls per collect, no mixing)
- Export integrity + leak tests (artifact-only hashes, text-only scanning incl. JWT-like + Authorization markers)
- Wipe/forget semantics (deterministic deletion + logout)
- Origin/host/security headers (ALLOWED_ORIGINS allowlist, TrustedHost, nosniff/no-referrer/DENY)
- Uvicorn --no-access-log to prevent OAuth query param leakage
- Root pytest runner fix (pytest.ini pythonpath=backend + smoke test adjustments for local SQLite)

## How to validate (exact commands, in order)
1) `./dev-up.sh`
2) `docker compose exec api pytest`
3) `cd frontend && npm install && npm run build`
4) Host-run tests (no Docker):
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r backend/requirements.txt`
   - `pytest -q`
5) Follow the checklist in `VALIDATION_PLAN.md`

