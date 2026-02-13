# Validation Plan (Demo-Ready + Trust-Ready MVP)

This is the release-gating checklist for the self-hosted, local-only MVP.

## Scope For This Validation
### What We Will Verify
- OAuth correctness & safety for GitHub and Microsoft (state, denial/error handling, reconnect)
- Token/secret handling (no token logging, encrypted at rest, safe failure modes)
- Evidence determinism (collect twice; snapshots don’t mix; exactly 12 controls)
- Export integrity (zip contents + manifest hashing verification)
- Data deletion correctness (Forget provider; Wipe all data)
- CSRF correctness for cookie-authenticated SPA
- Denmark procurement trust posture in report/README/demo script (DK/EN + data handling statement)

### What We Will Change (If Validation Fails)
- Error handling for OAuth callbacks (no 422/raw stack traces; user-readable)
- Determinism bugs (ensure each collection run writes a complete 12-control snapshot)
- Forget/Wipe semantics to be deterministic and complete
- CSRF/origin checks to be consistent and not placebo
- Report content to include required DK/EN headings + data handling statement (no secrets)

### What We Will Not Change
- No SaaS; no telemetry; no external analytics
- No LLM calls; no “AI” text generation
- No new providers or new controls beyond the existing 12
- No background jobs/schedulers; collection stays manual (“Collect now”)

## Preconditions
1. Docker Desktop installed (for `docker compose`)
2. OAuth apps created and redirect URIs configured
   - GitHub OAuth App callback:
     - `http://localhost:8000/api/oauth/github/callback`
   - Microsoft Entra app redirect URI:
     - `http://localhost:8000/api/oauth/microsoft/callback`
3. `.env` populated (copy from `.env.example`) and includes:
   - `DATABASE_URL`
   - `FERNET_KEY`
   - OAuth client IDs/secrets

## Static Checks (Local)
### Backend syntax/type sanity
```sh
python3 -m compileall -q backend/app backend/tests backend/alembic
```
Expected: exit code 0.

### Backend tests
```sh
cd backend
DATABASE_URL="sqlite+pysqlite:///:memory:" \
FERNET_KEY="$(python3 -c 'import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')" \
pytest
```
Expected: all tests pass.

### Frontend lint/build (optional but recommended)
```sh
cd frontend
npm install
npm run lint
npm run build
```
Expected: lint passes; build succeeds.

## End-to-End Runtime Validation (Docker Compose)
### Boot
```sh
./scripts/dev-up.sh
```
Expected:
- `web` available at `http://localhost:5173`
- `api` health check: `http://localhost:8000/api/health` returns `{"status":"ok"}`

### Auth + CSRF
1. In browser:
   - Register a new user
   - Confirm you can see Dashboard
2. Verify cookies (DevTools Application tab):
   - `dkpack_session` is HttpOnly
   - `dkpack_csrf` is readable by JS

Expected:
- Mutating actions work only when CSRF token is present (normal app usage).

## OAuth Correctness & Safety
### GitHub: success path
1. UI: `Connect` page → `Connect GitHub` → authorize
Expected:
- Redirect returns to `/connections` and shows GitHub as Connected
- No duplicate/stale connection rows (reconnect works cleanly after forget)

### GitHub: denial/error path
1. UI: `Connect GitHub` → click “Cancel”/deny
Expected:
- UI shows user-readable error (no 422 validation error page; no stack trace)
- No token saved; connection stays Not connected
- OAuth state is one-time (re-using callback URL does not connect)

### Microsoft: success path
1. UI: `Connect Microsoft` → authorize
Expected:
- Redirect returns to `/connections` and shows Microsoft as Connected

### Microsoft: missing admin consent / denial
1. Attempt connect in a tenant without required admin consent, or deny consent
Expected:
- UI shows user-readable error
- Controls dependent on missing scopes become `unknown` during collect (not a crash)
- No stack traces exposed

### Reconnect behavior (both providers)
1. UI: Forget provider → Connect again
Expected:
- Reconnect succeeds
- No leftover stale tokens

## Evidence Determinism
### Collect twice
1. UI: Dashboard → `Collect now`
2. UI: Dashboard → `Collect now` again
Expected:
- Dashboard always shows exactly 12 controls
- Latest collection produces a complete snapshot (no mixing across runs)
- Control details show latest artifacts and timestamps consistent with last run

## Export Integrity + “No Secrets In Exports”
### Export pack structure
1. UI: Dashboard → `Export pack (ZIP)`
2. Unzip and verify contents:
```sh
unzip -l dk-security-pack.zip
```
Expected: includes:
- `report.md`
- `report.pdf`
- `evidence-pack.zip`

### Evidence ZIP manifest + hash verification
```sh
unzip -p dk-security-pack.zip evidence-pack.zip > evidence-pack.zip
unzip -p evidence-pack.zip manifest.json > manifest.json
python3 - << 'PY'
import hashlib, json, zipfile
z = zipfile.ZipFile("evidence-pack.zip")
m = json.loads(z.read("manifest.json").decode("utf-8"))
bad = []
for f in m["files"]:
  data = z.read(f["filename"])
  got = hashlib.sha256(data).hexdigest()
  if got != f["sha256"]:
    bad.append((f["filename"], f["sha256"], got))
print("bad_hashes", bad)
print("ok" if not bad else "FAIL")
PY
```
Expected:
- `bad_hashes []`
- prints `ok`

### Confirm exports contain no secrets/tokens
```sh
python3 - << 'PY'
import zipfile, re
outer = zipfile.ZipFile("dk-security-pack.zip")
inner_bytes = outer.read("evidence-pack.zip")
open("evidence-pack.zip","wb").write(inner_bytes)
inner = zipfile.ZipFile("evidence-pack.zip")
blob = inner.read("manifest.json") + b"".join(inner.read(f["filename"]) for f in __import__("json").loads(inner.read("manifest.json"))["files"])
patterns = [rb"access_token", rb"refresh_token", rb"client_secret", rb"Bearer\\s+[A-Za-z0-9_\\-]+"]
hits = []
for p in patterns:
  if re.search(p, blob, flags=re.IGNORECASE):
    hits.append(p.decode("utf-8"))
print("hits:", hits)
print("ok" if not hits else "FAIL")
PY
```
Expected:
- `hits: []`
- prints `ok`

## Forget Provider / Wipe All Data
### Forget provider
1. UI: Connect → Forget GitHub (or Microsoft)
Expected:
- Provider connection becomes Not connected
- Stored tokens are deleted
- Provider evidence is deterministically cleared (dashboard controls move to `unknown` for that provider)

### Wipe all data
1. UI: Connect → Wipe all data
Expected:
- Connections cleared
- Evidence cleared (dashboard shows `unknown` / “No evidence”)
- Session is revoked/logged out (or equivalent explicit behavior)

