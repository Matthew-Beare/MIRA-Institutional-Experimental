#!/usr/bin/env python3
"""Generate and validate the hierarchical machine-readable Personal Ops Planner feature catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SOURCE_PATH = Path("docs/feature-ledger-2026-08-24.md")
JSON_PATH = Path("docs/feature-catalog.json")
MARKDOWN_PATH = Path("docs/feature-catalog.md")

# A matching path is CI evidence for the executable core only.  Provider state,
# permissions, live firing, and deployment readback remain separate release gates.
EVIDENCE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (r"exactly two briefs|canonical-clock|standalone scheduled|deterministic home/road|active trip tracking|multi-leg routes|company-paid mileage|phase-aware run log|optional module failure|briefs/action digest|work-trip/route/paid-work", (
        "skill/ops-brief-policy/scripts/ops_policy.py",
        "skill/ops-brief-policy/scripts/test_ops_policy.py",
        "skill/ops-brief-policy/scripts/test_ops_policy_entry.py",
    )),
    (r"ordered→shipped→delivered|active undelivered-only", (
        "skill/ops-brief-policy/scripts/reconcile_shipments.py",
        "skill/ops-brief-policy/scripts/test_reconcile_shipments.py",
        "skill/ops-brief-policy/scripts/test_reconcile_shipments_ordering.py",
    )),
    (r"expected-charge|refund, reimbursement|payment cases|personal finance organization", (
        "skill/ops-brief-policy/scripts/financial_resolution.py",
        "skill/ops-brief-policy/scripts/payment_reconciliation.py",
        "skill/ops-brief-policy/scripts/test_financial_resolution.py",
        "skill/ops-brief-policy/scripts/test_payment_reconciliation.py",
    )),
    (r"stable asset identity|immutable inventory/item ids|asset purchase evidence|knowledge ingestion|bidirectional receipt|namespaced upc|product/serial/barcode|manual discovery|vehicle/equipment technical|searchable expandable receipt", (
        "skill/ops-brief-policy/scripts/inventory_reconciliation.py",
        "skill/ops-brief-policy/scripts/asset_evidence.py",
        "skill/ops-brief-policy/scripts/test_inventory_reconciliation.py",
        "skill/ops-brief-policy/scripts/test_asset_evidence.py",
    )),
    (r"appointment reminder|appointments/calendar/reminders|medication reminders|caregiver reminder|administrative health organization", (
        "skill/ops-brief-policy/scripts/reminder_policy.py",
        "skill/ops-brief-policy/scripts/test_reminder_policy.py",
    )),
    (r"generic quarantined starter|standalone clean starter repository", (
        "scripts/audit_starter_privacy.py",
        "tests/test_starter_privacy_audit.py",
        "tests/test_public_source_audit.py",
    )),
    (r"adaptive first boot|explicit service activation|working and self-employed|retired/retiree|nonworking/between-jobs|parent/guardian|child/dependent|caregiver and household-manager|student profile|mixed/custom roles|older-adult usability", (
        "starter/tools/onboarding_profile_router.py",
        "starter/tests/test_onboarding_profile_router.py",
    )),
    (r"personal fork plus reviewed upstream", (
        "starter/tests/test_personal_fork_lifecycle.py",
        "starter/tests/test_feature_isolation_contracts.py",
    )),
    (r"browser-only non-technical installation|independent chatgpt github read", (
        "starter/INSTALL.md",
        "starter/install-flow.json",
        "starter/tests/test_nontechnical_installation.py",
    )),
    (r"provider-neutral ai runtime|personal git, organization git|google workspace and microsoft 365|apple/icloud and portable-file|locked-down and regulated enterprise", (
        "starter/platform-capabilities.json",
        "starter/tools/provider_capability_router.py",
        "starter/tests/test_platform_portability.py",
        "starter/PLATFORM_PORTABILITY.md",
        "starter/ENTERPRISE_PILOT.md",
    )),
    (r"laundry stages and drop-off/pickup reminders", (
        "starter/questions.json",
        "starter/tools/onboarding_profile_router.py",
        "starter/tests/test_onboarding_profile_router.py",
        "starter/tests/test_nontechnical_installation.py",
    )),
    (r"receipt intake from email", (
        "skill/ops-brief-policy/scripts/asset_evidence.py",
        "skill/ops-brief-policy/scripts/test_asset_evidence.py",
        "skill/ops-brief-policy/references/receipt-photo-intake.md",
    )),
    (r"hierarchical machine-readable feature catalog", (
        "scripts/feature_catalog.py",
        "tests/test_feature_catalog.py",
    )),
    (r"machine-enforced production-code inventory", (
        "docs/code-inventory.json",
        "tests/test_code_inventory.py",
    )),
)


def _cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    escaped = False
    for char in body:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def _delivery(status: str, decision: str) -> str:
    value = f"{status} {decision}".lower()
    if "rejected" in value:
        return "rejected"
    if "not present" in value or "paused historical" in value:
        return "not_present"
    if "infra" in value or "architecture doc" in value:
        return "infrastructure"
    if "spec-only" in value or "catalog only" in value or "backlog" in value:
        return "specification"
    if "contract-only" in value:
        return "contract"
    if "live external authority" in value or status.strip().lower() == "in use":
        return "live_external"
    if any(term in value for term in ("executable", "implemented and tested", "implemented as", "repaired")):
        return "executable"
    if "skill workflow" in value or "policy/skill behavior" in value:
        return "workflow"
    if any(term in value for term in ("partial", "candidate", "branch", "contract/skill")):
        return "mixed"
    if "unproven" in value:
        return "unproven"
    return "documented"


def _evidence(title: str) -> list[str]:
    lower = title.lower()
    output: list[str] = []
    for pattern, paths in EVIDENCE_RULES:
        if re.search(pattern, lower):
            output.extend(path for path in paths if path not in output)
    return output


def parse_ledger(source: str) -> list[dict[str, Any]]:
    categories: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_ledger = False
    row_number = 0
    for line in source.splitlines():
        if line == "## Consolidated feature ledger":
            in_ledger = True
            continue
        if line == "## Explicit exclusions and non-negotiable safety boundaries":
            break
        if not in_ledger:
            continue
        category_match = re.fullmatch(r"### ([A-G])\. (.+)", line)
        if category_match:
            current = {
                "id": category_match.group(1).lower(),
                "title": category_match.group(2),
                "features": [],
            }
            categories.append(current)
            row_number = 0
            continue
        if not current or not line.startswith("|"):
            continue
        cells = _cells(line)
        if not cells or cells[0] in {"Feature", "Service"} or set(cells[0]) <= {"-", ":"}:
            continue
        if len(cells) not in {3, 4}:
            raise ValueError(f"unsupported feature-ledger row: {line}")
        row_number += 1
        title, decision, status = cells[:3]
        disposition = cells[3] if len(cells) == 4 else ""
        evidence = _evidence(title)
        delivery = _delivery(status, decision)
        current["features"].append({
            "id": f"{current['id']}-{row_number:02d}",
            "title": title,
            "decision": decision,
            "delivery": delivery,
            "verification": "ci_evidence" if evidence else (
                "live_readback_required" if delivery == "live_external" else "documented"
            ),
            "current_status": status,
            "required_disposition": disposition,
            "evidence_paths": evidence,
        })
    return categories


def build(root: Path) -> dict[str, Any]:
    source_path = root / SOURCE_PATH
    source = source_path.read_text(encoding="utf-8")
    return {
        "schema_version": SCHEMA_VERSION,
        "catalog_version": "2026-08-25.1",
        "source": SOURCE_PATH.as_posix(),
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "maintenance_rule": "Update the forensic ledger, regenerate this catalog, and commit tests/evidence for every delivery claim.",
        "status_warning": "CI evidence verifies repository behavior only; live provider deployment, permissions, scheduler firing, and mutable-state readback are separate gates.",
        "categories": parse_ledger(source),
    }


def validate(catalog: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    categories = catalog.get("categories")
    if not isinstance(categories, list) or [row.get("id") for row in categories] != list("abcdefg"):
        errors.append("catalog must contain ordered categories a through g")
        return errors
    features = [feature for category in categories for feature in category.get("features", [])]
    ids = [feature.get("id") for feature in features]
    if len(features) < 60:
        errors.append(f"catalog is unexpectedly shallow: {len(features)} features")
    if len(ids) != len(set(ids)):
        errors.append("catalog contains duplicate feature IDs")
    allowed_delivery = {
        "rejected", "not_present", "infrastructure", "specification", "contract",
        "live_external", "executable", "workflow", "mixed", "unproven", "documented",
    }
    for feature in features:
        feature_id = feature.get("id", "unknown")
        if not _text(feature.get("title")):
            errors.append(f"{feature_id} has a blank title")
        if feature.get("delivery") not in allowed_delivery:
            errors.append(f"{feature_id} has invalid delivery state")
        evidence = feature.get("evidence_paths")
        if not isinstance(evidence, list):
            errors.append(f"{feature_id} evidence_paths is not a list")
            continue
        for relative in evidence:
            if not (root / relative).is_file():
                errors.append(f"{feature_id} evidence path is missing: {relative}")
        if feature.get("verification") == "ci_evidence" and not evidence:
            errors.append(f"{feature_id} claims CI evidence without an evidence path")
    return errors


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def render_markdown(catalog: dict[str, Any]) -> str:
    lines = [
        "# Personal Ops Planner hierarchical feature catalog",
        "",
        "Generated from `docs/feature-ledger-2026-08-24.md`. Edit the forensic ledger, "
        "then run `python3 scripts/feature_catalog.py --write`. CI rejects drift. Delivery "
        "status and verification are separate: repository tests do not prove a live "
        "connector or scheduled firing.",
        "",
    ]
    for category in catalog["categories"]:
        lines.extend((f"## {category['id'].upper()}. {category['title']}", "", "| ID | Feature | Decision | Delivery | Verification |", "|---|---|---|---|---|"))
        for feature in category["features"]:
            clean = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| `{feature['id']}` | {clean(feature['title'])} | {clean(feature['decision'])} | `{feature['delivery']}` | `{feature['verification']}` |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _json(catalog: dict[str, Any]) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        catalog = build(root)
        errors = validate(catalog, root)
        if errors:
            raise ValueError("; ".join(errors))
        expected_json = _json(catalog)
        expected_markdown = render_markdown(catalog)
        if args.write:
            (root / JSON_PATH).write_text(expected_json, encoding="utf-8")
            (root / MARKDOWN_PATH).write_text(expected_markdown, encoding="utf-8")
            print(f"wrote {JSON_PATH} and {MARKDOWN_PATH}")
            return 0
        actual_json = (root / JSON_PATH).read_text(encoding="utf-8")
        actual_markdown = (root / MARKDOWN_PATH).read_text(encoding="utf-8")
        if actual_json != expected_json or actual_markdown != expected_markdown:
            raise ValueError("feature catalog drift; run scripts/feature_catalog.py --write")
        print("feature catalog valid")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
