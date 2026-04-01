# Sample Security Pack — Vendor B (Anonymized)

> **DEMO — NOT FOR SUBMISSION**
> This is a sanitized example showing the output for a GitHub-only vendor.

## Pack Contents

| Artifact               | Format   | Description                            |
| ---------------------- | -------- | -------------------------------------- |
| `security_overview.md` | Markdown | Organization security posture          |
| `github_evidence.md`   | Markdown | GitHub security configuration evidence |
| `control_mapping.md`   | Markdown | ISO 27001 Annex A → evidence mapping   |

## GitHub Security Evidence (Excerpt)

**Repository**: acme-software/billing-service
**Scan Date**: 2026-03-10

| Control           | Finding                                                  | Status      |
| ----------------- | -------------------------------------------------------- | ----------- |
| Branch Protection | `main`: require 2 reviews, status checks, signed commits | ✅ Enforced |
| Dependabot        | Auto-security updates enabled, 0 critical alerts         | ✅ Clean    |
| Secret Scanning   | Push protection enabled, 0 active alerts                 | ✅ Clean    |
| CodeQL            | Weekly analysis, 0 high/critical findings                | ✅ Clean    |
| CODEOWNERS        | Defined for `/src`, `/infra`, `/docs`                    | ✅ Present  |

## ISO 27001 Annex A Mapping (Excerpt)

| Control | Title                        | Evidence                                               | Status |
| ------- | ---------------------------- | ------------------------------------------------------ | ------ |
| A.8.9   | Configuration management     | `github_evidence.md` — branch protection, CODEOWNERS   | ✅     |
| A.8.25  | Secure development lifecycle | `github_evidence.md` — CodeQL, Dependabot              | ✅     |
| A.8.28  | Secure coding                | `github_evidence.md` — secret scanning, signed commits | ✅     |
