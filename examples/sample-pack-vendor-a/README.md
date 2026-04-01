# Sample Security Pack — Vendor A (Anonymized)

> **DEMO — NOT FOR SUBMISSION**
> This is a sanitized example showing the output format of a DK Procurement Security Pack.

## Pack Contents

| Artifact                 | Format   | Description                              |
| ------------------------ | -------- | ---------------------------------------- |
| `security_overview.md`   | Markdown | Organization security posture summary    |
| `control_mapping.md`     | Markdown | NIS2 Article → evidence artifact mapping |
| `evidence_manifest.json` | JSON     | SHA-256 hashed evidence inventory        |

## Security Overview (Excerpt)

**Organization**: Acme Software ApS (fictional)
**Assessment Date**: 2026-03-15
**Framework**: NIS2 Directive, ISO/IEC 27001:2022

### Access Control

- Azure Entra ID with MFA enforced for all users
- Role-based access control with quarterly access reviews
- Privileged access managed via PIM with 4-hour activation windows

### Source Code Security

- GitHub Advanced Security enabled (Dependabot, CodeQL, secret scanning)
- Branch protection: 2 reviewer minimum, status checks required
- Signed commits enforced on main branch

### Infrastructure

- Azure West Europe region, data residency within EU
- Encryption at rest (AES-256) and in transit (TLS 1.3)
- Network segmentation with NSG rules, no public-facing databases

## NIS2 Control Mapping (Excerpt)

| NIS2 Article  | Requirement                                   | Evidence Artifact                  | Status     |
| ------------- | --------------------------------------------- | ---------------------------------- | ---------- |
| Art. 21(2)(a) | Risk analysis and information system security | `risk_assessment_2026_q1.pdf`      | ✅ Current |
| Art. 21(2)(b) | Incident handling                             | `incident_response_plan_v3.pdf`    | ✅ Current |
| Art. 21(2)(d) | Supply chain security                         | `vendor_risk_register.xlsx`        | ✅ Current |
| Art. 21(2)(e) | Security in network and information systems   | `network_architecture_diagram.pdf` | ✅ Current |
| Art. 21(2)(j) | Use of cryptography and encryption            | `encryption_policy_v2.pdf`         | ✅ Current |
