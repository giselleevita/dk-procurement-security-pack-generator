# 3-Minute Demo Script (Click-by-Click + Narration)

Goal: demonstrate a Denmark procurement-ready, **local-only** security documentation pack generated from real evidence (GitHub + Microsoft Graph), with clear trust posture and safety actions.

## Setup (Before the Demo)
- App is running locally:
  - `./dev-up.sh`
- You have a GitHub OAuth App and a Microsoft Entra app configured in `.env`.
- You have a test user ready (or register during demo).

## Script (3 minutes)

### 0:00–0:20 — Trust posture opener (Denmark wedge)
Say:
- “Procurement in Denmark often asks for a vendor security documentation pack with evidence.”
- “This tool generates that pack **locally**, self-hosted, with **no SaaS**, **no telemetry**, and **no external analytics**.”
- “Everything you see is deterministic and derived from evidence pulled from your Microsoft 365 tenant and GitHub.”

Click:
- Open `http://localhost:5173`

### 0:20–0:45 — Local auth (no shared vendor accounts)
Click:
- Register (or Login)

Say:
- “Local user auth, session via **HttpOnly cookies**.”
- “This is designed to avoid security-clearance or trust concerns: data stays in your environment.”

### 0:45–1:30 — Connect providers (OAuth + encrypted tokens)
Click:
- Top nav → `Connect`
- `Connect GitHub` → authorize
- `Connect Microsoft` → authorize

Say:
- “OAuth tokens are stored **encrypted at rest** in Postgres (Fernet).”
- “We do not log tokens. We only call GitHub/Graph when you explicitly collect evidence.”
- “If admin consent is missing in Microsoft, we don’t crash; we mark controls as Unknown and explain why.”
- “After OAuth you return to `/connections?provider=...&status=connected` (or `status=error&error=...`).”

### 1:30–2:10 — Collect evidence and show control detail
Click:
- Top nav → `Dashboard`
- `Collect now`
- Click one GitHub control (example: Branch protection)

Say:
- “We evaluate a small set of procurement-friendly controls: green/yellow/red.”
- “Control detail shows deterministic notes and the raw JSON artifacts so a procurement reviewer can verify evidence.”

### 2:10–2:40 — Export the procurement pack (MD + PDF + evidence ZIP)
Click:
- `Export pack (ZIP)`

Say:
- “Download name is `dk-security-pack.zip` and it includes `report.md`, `report.pdf`, and `evidence-pack.zip`.”
- “`evidence-pack.zip` contains `manifest.json` and `artifacts/*.json`, with **SHA-256 hashes** so integrity is verifiable.”
- “No secrets are included in the export packs: no tokens, no client secrets.”

### 2:40–3:00 — Safety actions (Forget provider + Wipe all data)
Click:
- Top nav → `Connect`
- `Forget GitHub` (or Microsoft)
- `Wipe all data`

Say:
- “Forget provider deletes stored tokens and clears provider evidence deterministically.”
- “Wipe all data deletes evidence, connections, oauth states, and sessions, and logs you out. This is a local system; you can always purge it.”
- “That’s the procurement trust posture: local-only, evidence-based, and easy to audit.”

## Denmark Procurement Pitch Lines (Use as Needed)
- “We’re optimized for the Danish procurement workflow: a bilingual DK/EN pack with verifiable evidence.”
- “Self-hosted by default to avoid vendor trust and clearance issues.”
- “Deterministic output: no AI-generated claims, only evidence-backed statements.”
