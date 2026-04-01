from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repos.evidence import latest_evidence_all_controls
from app.services.control_defs import CONTROLS
from app.services.framework_mappings import CONTROL_FRAMEWORK_MAP, ISO27001_CLAUSE_LABELS, NIS2_ARTICLE_LABELS


def build_framework_gap_report(db: Session, *, user_id: uuid.UUID) -> dict:
    latest = {row.control_key: row for row in latest_evidence_all_controls(db, user_id=user_id)}

    controls_by_key = {c.key: c for c in CONTROLS}

    framework_entries: list[dict] = []
    for framework, label_map in (("nis2", NIS2_ARTICLE_LABELS), ("iso27001", ISO27001_CLAUSE_LABELS)):
        refs: dict[str, dict] = {}
        for control in CONTROLS:
            status = (latest.get(control.key).status if latest.get(control.key) else "unknown").lower()
            mapping = CONTROL_FRAMEWORK_MAP.get(control.key, {}).get(framework, ())
            for ref in mapping:
                if ref not in refs:
                    refs[ref] = {
                        "reference": ref,
                        "label": label_map.get(ref, ref),
                        "total_controls": 0,
                        "passing_controls": 0,
                        "gap_controls": [],
                    }
                refs[ref]["total_controls"] += 1
                if status == "pass":
                    refs[ref]["passing_controls"] += 1
                else:
                    refs[ref]["gap_controls"].append(control.key)

        framework_entries.extend(refs.values())

    priority_gaps: list[dict] = []
    for control in CONTROLS:
        status = (latest.get(control.key).status if latest.get(control.key) else "unknown").lower()
        if status == "pass":
            continue
        mapping = CONTROL_FRAMEWORK_MAP.get(control.key, {})
        priority_gaps.append(
            {
                "control_key": control.key,
                "title_en": control.title_en,
                "status": status,
                "nis2_refs": list(mapping.get("nis2", ())),
                "iso27001_refs": list(mapping.get("iso27001", ())),
            }
        )

    priority_gaps.sort(key=lambda item: (0 if item["status"] == "unknown" else 1, item["control_key"]))

    total_controls = len(CONTROLS)
    passing_controls = 0
    unknown_controls = 0
    for control in CONTROLS:
        status = (latest.get(control.key).status if latest.get(control.key) else "unknown").lower()
        if status == "pass":
            passing_controls += 1
        if status == "unknown":
            unknown_controls += 1

    return {
        "summary": {
            "total_controls": total_controls,
            "passing_controls": passing_controls,
            "gap_controls": total_controls - passing_controls,
            "unknown_controls": unknown_controls,
        },
        "frameworks": framework_entries,
        "priority_gaps": priority_gaps,
        "generated_from_control_set": sorted(controls_by_key.keys()),
    }