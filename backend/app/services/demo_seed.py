"""Demo seed: creates a realistic demo user + vendor profile + attestations + snapshot.

Only called at startup when APP_ENV=demo. Safe to call multiple times (idempotent).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repos.attestations import upsert_attestation
from app.repos.evidence import latest_run
from app.repos.users import create_user, get_user_by_email
from app.repos.vendor_profile import get_vendor_profile, upsert_vendor_profile
from app.services.collect import write_demo_snapshot

log = logging.getLogger(__name__)

_DEMO_VENDOR = {
    "company_name": "CloudSec ApS",
    "cvr_number": "33445566",
    "address": "Rådhuspladsen 77, 1550 København V",
    "contact_name": "Lars Andersen",
    "contact_email": "lars@cloudsec.dk",
    "contact_phone": "+45 70 12 34 56",
    "security_officer_name": "Maria Jensen",
    "security_officer_title": "Chief Information Security Officer",
    "pack_scope": (
        "Cloud platform security for SaaS procurement — "
        "Microsoft 365, GitHub source control, and cloud infrastructure."
    ),
    "pack_recipient": "Indkøbsafdelingen, Aarhus Kommune",
    "pack_validity_months": 6,
}

_DEMO_ATTESTATIONS = [
    {
        "control_key": "att.incident_response",
        "status": "pass",
        "notes": (
            "IR plan v3.1 approved January 2025. "
            "Tabletop exercise completed Q4 2025. "
            "Plan reviewed annually by CISO and Legal."
        ),
        "attested_by": "Maria Jensen",
    },
    {
        "control_key": "att.backup_and_recovery",
        "status": "pass",
        "notes": (
            "Daily automated backups to geographically separated region (eu-west-1). "
            "RTO 4 h, RPO 1 h — last tested 2025-11-14 with successful restore."
        ),
        "attested_by": "Maria Jensen",
    },
    {
        "control_key": "att.encryption_at_rest_in_transit",
        "status": "pass",
        "notes": (
            "AES-256 encryption at rest for all datastores. "
            "TLS 1.2+ enforced in transit; TLS 1.0/1.1 disabled. "
            "Certificates managed via cert-manager with auto-rotation."
        ),
        "attested_by": "Maria Jensen",
    },
    {
        "control_key": "att.endpoint_management",
        "status": "pass",
        "notes": (
            "All corporate endpoints enrolled in Microsoft Intune. "
            "EDR via Microsoft Defender for Endpoint. "
            "Non-compliant devices blocked from corporate resources."
        ),
        "attested_by": "Maria Jensen",
    },
    {
        "control_key": "att.vulnerability_management",
        "status": "pass",
        "notes": (
            "Snyk integrated in CI pipeline — builds fail on critical CVEs. "
            "Dependabot alerts enabled on all GitHub repos. "
            "Monthly infrastructure scan with remediation SLA: Critical 48 h, High 14 d."
        ),
        "attested_by": "Maria Jensen",
    },
    {
        "control_key": "att.gdpr_dpa",
        "status": "pass",
        "notes": (
            "DPA in place with all sub-processors (AWS, Microsoft, GitHub). "
            "DPO appointed: dpo@cloudsec.dk. "
            "Sub-processor list published at cloudsec.dk/subprocessors."
        ),
        "attested_by": "Maria Jensen",
    },
]


def seed_demo_data(db: Session, *, demo_email: str, demo_password: str) -> None:
    """Idempotently seed the demo user, vendor profile, attestations, and evidence snapshot."""
    # 1. Ensure demo user exists.
    user = get_user_by_email(db, demo_email)
    if user is None:
        log.info("Demo seed: creating demo user %s", demo_email)
        user = create_user(db, email=demo_email, password_hash=hash_password(demo_password))
    else:
        log.info("Demo seed: demo user already exists")

    user_id = user.id

    # 2. Seed vendor profile (only if empty).
    vp = get_vendor_profile(db, user_id=user_id)
    if vp is None or not vp.company_name:
        log.info("Demo seed: seeding vendor profile")
        upsert_vendor_profile(db, user_id=user_id, data=_DEMO_VENDOR)

    # 3. Seed attestations.
    attested_at = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    for att in _DEMO_ATTESTATIONS:
        upsert_attestation(
            db,
            user_id=user_id,
            control_key=att["control_key"],
            status=att["status"],
            notes=att["notes"],
            attested_by=att["attested_by"],
            attested_at=attested_at,
        )
    log.info("Demo seed: attestations seeded")

    # 4. Write a demo evidence snapshot (skip if one already exists).
    run = latest_run(db, user_id=user_id)
    if run is None:
        log.info("Demo seed: writing demo evidence snapshot")
        write_demo_snapshot(db, user_id=user_id)
    else:
        log.info("Demo seed: evidence snapshot already exists, skipping")
