# Sample Security Pack — Vendor C (Anonymized)

> **DEMO — NOT FOR SUBMISSION**
> This is a sanitized example showing the output for a Microsoft 365 + GitHub combined vendor.

## Pack Contents

| Artifact               | Format   | Description                                |
| ---------------------- | -------- | ------------------------------------------ |
| `security_overview.md` | Markdown | Combined M365 + GitHub security posture    |
| `m365_evidence.md`     | Markdown | Microsoft 365 / Entra ID security evidence |
| `github_evidence.md`   | Markdown | GitHub repository security evidence        |
| `control_mapping.md`   | Markdown | DS 484 + NIS2 combined mapping             |
| `pack_signature.json`  | JSON     | Ed25519 signature over all artifacts       |

## Microsoft 365 / Entra Evidence (Excerpt)

**Tenant**: acme-consulting.onmicrosoft.com
**Scan Date**: 2026-03-20

| Control            | Finding                                              | Status |
| ------------------ | ---------------------------------------------------- | ------ |
| MFA                | Enforced for all users via Conditional Access        | ✅     |
| Conditional Access | 3 policies active (MFA, device compliance, location) | ✅     |
| PIM                | Enabled for Global Admin, Security Admin roles       | ✅     |
| Audit Logging      | Unified audit log enabled, 365-day retention         | ✅     |
| DLP                | 2 active policies (credit card, personal ID numbers) | ✅     |

## Pack Signature (Excerpt)

```json
{
  "algorithm": "Ed25519",
  "signed_at": "2026-03-20T14:30:00Z",
  "artifacts_hash": "sha256:9f86d08...",
  "signer": "dk-pack-generator v1.0",
  "verification": "Use `dkpack verify pack_signature.json` to validate"
}
```
