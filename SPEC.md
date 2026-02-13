# DK Procurement Security Pack Generator (Self-hosted) — MVP Spec

## Problem
Danish public procurement (and many private vendor risk reviews) often requires a vendor to provide a security documentation “pack” with concrete, verifiable evidence: identity provider configuration, access control posture, and SDLC / repo protections. For small teams, assembling this pack is repetitive, error-prone, and time-consuming, especially when evidence must be updated for each tender.

This product generates a procurement-ready security documentation pack locally (self-hosted) from:
- Microsoft 365 / Entra evidence via Microsoft Graph
- GitHub evidence via GitHub API

No data is sent to third-party services. Output is deterministic and derived only from collected evidence.

## Goals
- Generate a DK/EN vendor security documentation pack with evidence artifacts and a simple dashboard (12 controls max).
- Run locally via Docker Compose; no SaaS, no telemetry, no external analytics.
- Least-privilege OAuth, encrypted token storage, and safe handling of secrets and exports.
- Strong 3-minute demo path: connect providers → collect → dashboard → export ZIP/PDF.

## Non-Goals (MVP Out of Scope)
- Any LLM/AI generated narrative beyond deterministic templates.
- Continuous monitoring, scheduled collection, background workers.
- Remediation or configuration changes in GitHub/Microsoft.
- Multi-tenant SaaS, hosted offering, telemetry, or “phone home”.
- Deep compliance frameworks (NIS2/ISO mapping), custom control authoring.
- Evidence from other systems (Azure, AWS, Jira, GitLab, Okta, etc.).

## Personas
- Vendor Security Owner (small/medium software vendor): needs a repeatable pack for tenders; wants evidence freshness.
- Engineering Lead/DevOps: wants minimal disruption; prefers “one button collect” and accurate, inspectable artifacts.
- Procurement Reviewer (DK/EN): wants clear headings, simple pass/warn/fail, and a complete evidence archive.

## Primary Workflows
1. Local user signup/login
   - Create account with email + password
   - Login creates session stored via HttpOnly cookie

2. Connect accounts
   - Connect GitHub via OAuth App authorization code flow
   - Connect Microsoft (Entra) via OAuth authorization code flow for Microsoft Graph
   - Tokens stored encrypted at rest; no token logging; “Forget provider” action available

3. Collect now
   - Trigger evidence collection from connected providers
   - Store evidence per control as JSON artifacts and computed status (pass/warn/fail/unknown)
   - Only up to 10 GitHub repos sampled per run to keep MVP fast and rate-limit friendly

4. Dashboard
   - Show max 12 controls with green/yellow/red/gray and last-updated
   - “Evidence freshness” control flags stale data

5. Control detail
   - Show latest artifacts (raw JSON) + a deterministic note/explanation template

6. Export pack
   - Generate:
     - `report.md` (DK/EN headings)
     - `report.pdf` (simple rendering acceptable)
     - `evidence-pack.zip` including `manifest.json` + artifacts

7. Safety actions
   - Forget provider: delete tokens + provider connection for current user
   - Wipe all data: delete evidence + connections for current user

## MVP Control Set (Max 12)
All controls are procurement-friendly and reported with DK/EN headings.

### Microsoft (Graph)
1. Security Defaults enabled (if accessible): pass/warn/unknown
2. Conditional Access present (if accessible): pass/warn/unknown (based on policy count)
3. Admin surface area heuristic: warn/fail/unknown (directory roles count if accessible)

### GitHub
4. Branch protection present on default branch (sampled repos)
5. PR reviews required (sampled repos)
6. Force pushes disabled (sampled repos)
7. Admin enforcement enabled (sampled repos)
8. Repo visibility review: count public/private/internal; warn if public repos exist (heuristic)

### Pack Hygiene
9. Evidence freshness: pass/warn based on last collection time
10. Documentation completeness: pass/warn if missing key artifacts for any control
11. Export integrity: pass/warn if manifest references missing artifact files
12. Connection status: pass/warn if one provider missing (heuristic)

## MVP Success Criteria
- One-command local run via Docker Compose.
- Can create a user, connect both providers, collect evidence, view dashboard, and export pack.
- All exports are reproducible from stored evidence (no hidden derived text).
- Provider connections can be forgotten; user can wipe all data.
- Basic unit tests and an integration smoke test run locally.

