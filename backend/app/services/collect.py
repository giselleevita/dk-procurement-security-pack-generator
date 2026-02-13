from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.providers.github_api import GitHubApi, GitHubApiError
from app.providers.graph_api import GraphApi, GraphApiError
from app.repos.connections import get_connection
from app.repos.evidence import add_control_evidence, create_run, finish_run
from app.services.control_defs import CONTROLS
from app.services.tokens import TokenDecryptError, TokenExpiredError, get_github_access_token, get_microsoft_access_token


GITHUB_CONTROL_KEYS = (
    "gh.branch_protection",
    "gh.pr_reviews_required",
    "gh.force_pushes_disabled",
    "gh.enforce_admins",
    "gh.repo_visibility_review",
)

MICROSOFT_CONTROL_KEYS = (
    "ms.security_defaults",
    "ms.conditional_access_presence",
    "ms.admin_surface_area",
)


def collect_now(db: Session, *, user_id) -> dict:
    run = create_run(db, user_id=user_id)

    errors: list[str] = []

    # Always write a complete 12-control snapshot per run (no mixing across runs).
    try:
        _collect_github(db, user_id=user_id, run_id=run.id)
    except Exception as e:
        errors.append(f"github: {type(e).__name__}")
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run.id,
            keys=GITHUB_CONTROL_KEYS,
            provider="github",
            artifacts={"error": "github_collection_failed", "error_type": type(e).__name__},
            notes="GitHub evidence collection failed; reconnect or check permissions.",
        )

    try:
        _collect_microsoft(db, user_id=user_id, run_id=run.id)
    except Exception as e:
        errors.append(f"microsoft: {type(e).__name__}")
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run.id,
            keys=MICROSOFT_CONTROL_KEYS,
            provider="microsoft",
            artifacts={"error": "microsoft_collection_failed", "error_type": type(e).__name__},
            notes="Microsoft evidence collection failed; reconnect or check permissions/admin consent.",
        )

    # Pack hygiene controls computed from what we just stored.
    _collect_pack_hygiene(db, user_id=user_id, run_id=run.id)

    if errors:
        finish_run(db, run_id=run.id, status="partial", error_summary="; ".join(errors))
    else:
        finish_run(db, run_id=run.id, status="success", error_summary=None)

    return {"run_id": str(run.id), "status": "partial" if errors else "success", "errors": errors}


def _collect_github(db: Session, *, user_id, run_id) -> None:
    conn = get_connection(db, user_id=user_id, provider="github")
    if conn is None:
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run_id,
            keys=GITHUB_CONTROL_KEYS,
            provider="github",
            artifacts={"error": "github_not_connected"},
            notes="GitHub is not connected.",
        )
        return

    try:
        token = get_github_access_token(conn)
    except TokenDecryptError as e:
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run_id,
            keys=GITHUB_CONTROL_KEYS,
            provider="github",
            artifacts={"error": "github_token_decrypt_failed"},
            notes=str(e),
        )
        return
    api = GitHubApi(access_token=token)

    try:
        repos = api.list_repos(per_page=100)[:10]
    except Exception as e:
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run_id,
            keys=GITHUB_CONTROL_KEYS,
            provider="github",
            artifacts={"error": "github_repo_list_failed", "error_type": type(e).__name__},
            notes="Unable to list repositories with the current GitHub token/scopes; reconnect or adjust permissions.",
        )
        return
    if not repos:
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run_id,
            keys=GITHUB_CONTROL_KEYS,
            provider="github",
            artifacts={"repos_sampled": 0},
            notes="No repositories found for the connected GitHub account.",
        )
        return

    repo_rows: list[dict] = []
    visibility_counts = {"public": 0, "private": 0, "internal": 0, "unknown": 0}

    for r in repos:
        visibility = (r.visibility or "unknown").lower()
        visibility_counts[visibility] = visibility_counts.get(visibility, 0) + 1

        row = {"repo": r.full_name, "default_branch": r.default_branch, "visibility": visibility}
        try:
            protection = api.get_branch_protection(full_name=r.full_name, branch=r.default_branch)
        except GitHubApiError as e:
            row["error"] = str(e)
            row["branch_protection"] = None
            repo_rows.append(row)
            continue

        row["branch_protection"] = protection
        repo_rows.append(row)

    def _bool(obj: dict | None, path: list[str], *, default: bool = False) -> bool:
        cur = obj or {}
        for p in path:
            if not isinstance(cur, dict) or p not in cur:
                return default
            cur = cur[p]
        return bool(cur)

    per_repo = []
    for row in repo_rows:
        protection = row.get("branch_protection")
        protected = protection is not None
        pr_reviews = _bool(protection, ["required_pull_request_reviews"]) if protected else False
        # If the default branch is not protected, treat force pushes as effectively allowed for this control.
        allow_force_pushes = (
            _bool(protection, ["allow_force_pushes", "enabled"], default=False) if protected else True
        )
        enforce_admins = _bool(protection, ["enforce_admins", "enabled"], default=False) if protected else False
        per_repo.append(
            {
                "repo": row["repo"],
                "protected": protected,
                "pr_reviews_required": bool(pr_reviews),
                "force_pushes_allowed": bool(allow_force_pushes),
                "enforce_admins": bool(enforce_admins),
                "visibility": row.get("visibility"),
                "error": row.get("error"),
            }
        )

    n = len(per_repo)
    protected_n = sum(1 for x in per_repo if x["protected"])
    pr_reviews_n = sum(1 for x in per_repo if x["pr_reviews_required"])
    force_push_allowed_n = sum(1 for x in per_repo if x["force_pushes_allowed"])
    enforce_admins_n = sum(1 for x in per_repo if x["enforce_admins"])
    public_n = sum(1 for x in per_repo if x.get("visibility") == "public")

    branch_protection_status = _aggregate_status(n, protected_n, bad_count=(n - protected_n))
    pr_reviews_status = _aggregate_status(n, pr_reviews_n, bad_count=(n - pr_reviews_n))
    force_pushes_status = _aggregate_inverse_status(n, bad_count=force_push_allowed_n)
    enforce_admins_status = _aggregate_status(n, enforce_admins_n, bad_count=(n - enforce_admins_n))
    visibility_status = "warn" if public_n > 0 else "pass"

    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="gh.branch_protection",
        provider="github",
        status=branch_protection_status,
        artifacts={"repos_sampled": n, "protected": protected_n, "per_repo": per_repo, "visibility_counts": visibility_counts},
        notes=_notes_ratio("Branch protection enabled", protected_n, n),
    )
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="gh.pr_reviews_required",
        provider="github",
        status=pr_reviews_status,
        artifacts={"repos_sampled": n, "pr_reviews_required": pr_reviews_n, "per_repo": per_repo},
        notes=_notes_ratio("PR reviews required", pr_reviews_n, n),
    )
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="gh.force_pushes_disabled",
        provider="github",
        status=force_pushes_status,
        artifacts={"repos_sampled": n, "force_pushes_allowed": force_push_allowed_n, "per_repo": per_repo},
        notes="Force pushes should generally be disabled on protected branches.",
    )
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="gh.enforce_admins",
        provider="github",
        status=enforce_admins_status,
        artifacts={"repos_sampled": n, "enforce_admins_enabled": enforce_admins_n, "per_repo": per_repo},
        notes=_notes_ratio("Admin enforcement enabled", enforce_admins_n, n),
    )
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="gh.repo_visibility_review",
        provider="github",
        status=visibility_status,
        artifacts={"repos_sampled": n, "visibility_counts": visibility_counts, "public_repos_in_sample": public_n, "per_repo": per_repo},
        notes="Public repositories may expose code or metadata; review if public repos are intended.",
    )


def _collect_microsoft(db: Session, *, user_id, run_id) -> None:
    conn = get_connection(db, user_id=user_id, provider="microsoft")
    if conn is None:
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run_id,
            keys=MICROSOFT_CONTROL_KEYS,
            provider="microsoft",
            artifacts={"error": "microsoft_not_connected"},
            notes="Microsoft is not connected.",
        )
        return

    try:
        token = get_microsoft_access_token(db, conn)
    except (TokenDecryptError, TokenExpiredError) as e:
        _write_unknown_controls(
            db,
            user_id=user_id,
            run_id=run_id,
            keys=MICROSOFT_CONTROL_KEYS,
            provider="microsoft",
            artifacts={"error": "microsoft_token_invalid"},
            notes=str(e),
        )
        return
    api = GraphApi(access_token=token)

    artifacts: dict = {}
    try:
        org = api.get_org()
        artifacts["organization"] = asdict(org)
    except GraphApiError as e:
        artifacts["organization_error"] = {"status_code": e.status_code, "message": str(e)}

    # Security Defaults
    try:
        sd = api.get_security_defaults()
        enabled = bool(sd.get("isEnabled"))
        status_sd = "pass" if enabled else "warn"
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run_id,
            control_key="ms.security_defaults",
            provider="microsoft",
            status=status_sd,
            artifacts={"security_defaults": sd, **artifacts},
            notes="Security Defaults enabled is generally a baseline when Conditional Access is not configured.",
        )
    except GraphApiError as e:
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run_id,
            control_key="ms.security_defaults",
            provider="microsoft",
            status="unknown",
            artifacts={"error": {"status_code": e.status_code, "message": str(e)}, **artifacts},
            notes="Unable to read Security Defaults via Graph with current permissions.",
        )

    # Conditional Access presence
    try:
        ca_count = api.count_conditional_access_policies()
        status_ca = "pass" if ca_count > 0 else "warn"
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run_id,
            control_key="ms.conditional_access_presence",
            provider="microsoft",
            status=status_ca,
            artifacts={"conditional_access_policy_count": ca_count, **artifacts},
            notes="Conditional Access policies are a common control for enforcing MFA and access constraints.",
        )
    except GraphApiError as e:
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run_id,
            control_key="ms.conditional_access_presence",
            provider="microsoft",
            status="unknown",
            artifacts={"error": {"status_code": e.status_code, "message": str(e)}, **artifacts},
            notes="Unable to list Conditional Access policies via Graph with current permissions.",
        )

    # Admin surface area heuristic
    try:
        roles_count = api.count_directory_roles()
        # Heuristic: a very large number of active roles may correlate with complexity/risk.
        status_roles = "pass" if 1 <= roles_count <= 10 else "warn"
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run_id,
            control_key="ms.admin_surface_area",
            provider="microsoft",
            status=status_roles,
            artifacts={"directory_roles_count": roles_count, **artifacts},
            notes="Heuristic only: review privileged roles and assignments periodically.",
        )
    except GraphApiError as e:
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run_id,
            control_key="ms.admin_surface_area",
            provider="microsoft",
            status="unknown",
            artifacts={"error": {"status_code": e.status_code, "message": str(e)}, **artifacts},
            notes="Unable to read directory roles via Graph with current permissions.",
        )


def _collect_pack_hygiene(db: Session, *, user_id, run_id) -> None:
    latest_rows = {r.control_key: r for r in _latest_run_rows(db, user_id=user_id, run_id=run_id)}
    now = datetime.utcnow()

    # Evidence freshness: warn if newest evidence older than 7 days.
    newest = max((r.collected_at for r in latest_rows.values()), default=None)
    if newest is None:
        status = "unknown"
        artifacts = {"newest_collected_at": None}
        notes = "No evidence collected yet."
    else:
        stale = newest < (now - timedelta(days=7))
        status = "warn" if stale else "pass"
        artifacts = {"newest_collected_at": newest.isoformat() + "Z", "stale_days_threshold": 7}
        notes = "Evidence should be refreshed regularly for procurement processes."
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="pack.evidence_freshness",
        provider="pack",
        status=status,
        artifacts=artifacts,
        notes=notes,
    )

    # Documentation completeness: ensure all provider controls have evidence rows in this run.
    expected_provider = {c.key for c in CONTROLS if c.provider in ("github", "microsoft")}
    present = set(latest_rows.keys())
    missing = sorted(expected_provider - present)
    status = "pass" if not missing else "warn"
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="pack.documentation_completeness",
        provider="pack",
        status=status,
        artifacts={"missing_provider_controls": missing},
        notes="All controls should have evidence artifacts for a complete pack." if missing else "All controls have evidence rows.",
    )

    # Export integrity: validated during export.
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="pack.export_integrity",
        provider="pack",
        status="unknown",
        artifacts={"note": "Validated during export."},
        notes="Run export to validate manifest and artifact integrity.",
    )

    # Connection status
    gh = get_connection(db, user_id=user_id, provider="github")
    ms = get_connection(db, user_id=user_id, provider="microsoft")
    status = "pass" if (gh is not None and ms is not None) else "warn"
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run_id,
        control_key="pack.connection_status",
        provider="pack",
        status=status,
        artifacts={"github_connected": gh is not None, "microsoft_connected": ms is not None},
        notes="Both providers connected." if status == "pass" else "One or more providers are not connected.",
    )


def _latest_run_rows(db: Session, *, user_id, run_id):
    # Fetch all rows for this run.
    from sqlalchemy import select

    from app.models.evidence import ControlEvidence

    stmt = select(ControlEvidence).where(ControlEvidence.user_id == user_id, ControlEvidence.run_id == run_id)
    return list(db.execute(stmt).scalars().all())


def _write_unknown_controls(
    db: Session,
    *,
    user_id,
    run_id,
    keys: tuple[str, ...],
    provider: str,
    artifacts: dict,
    notes: str,
) -> None:
    for key in keys:
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run_id,
            control_key=key,
            provider=provider,
            status="unknown",
            artifacts=artifacts,
            notes=notes,
        )


def _aggregate_status(total: int, good: int, *, bad_count: int) -> str:
    if total <= 0:
        return "unknown"
    if good == total:
        return "pass"
    if bad_count == total:
        return "fail"
    return "warn"


def _aggregate_inverse_status(total: int, *, bad_count: int) -> str:
    if total <= 0:
        return "unknown"
    if bad_count == 0:
        return "pass"
    if bad_count == total:
        return "fail"
    return "warn"


def _notes_ratio(label: str, good: int, total: int) -> str:
    if total <= 0:
        return f"{label}: no repositories sampled."
    return f"{label}: {good}/{total} repositories in sample."
