# Signed security pack in 90 seconds

**0:00–0:15 — Problem.** Supplier-security reviews need portable evidence whose integrity can be checked without trusting the producing application.

**0:15–0:30 — Safe demo boundary.** Select **Try synthetic demo**. The public/free configuration is disposable, contains synthetic evidence, and disables sensitive integrations.

**0:30–1:05 — Golden path.** Select **Run verified demo**. The application collects the 12-control snapshot, creates a versioned manifest, hashes every artifact, signs it with Ed25519, and independently verifies the archive.

**1:05–1:20 — Negative proof.** The same journey modifies `report.md` in memory and verifies that the changed pack is rejected. Expand **Artifact fingerprints** to show the evidence identifiers.

**1:20–1:30 — Boundary.** The free demo uses ephemeral storage and keys. Production use requires durable PostgreSQL, managed key custody, backups, monitoring, and organization-specific assurance review.

## Interview prompts this supports

- What exactly is signed, and how is an unexpected archive member handled?
- How are tenant isolation and OAuth state enforced?
- Which guarantees disappear when signing keys and storage are ephemeral?
