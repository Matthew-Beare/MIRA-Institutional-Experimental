# MIRROR | MIRA

**MIRROR** is the personal reality layer. **MIRA** is the assistant that reasons over it.

> **MIRA, mirror on the wall.**

MIRROR is a version-controlled personal-operations framework for briefs, persistent state, receipts/orders, planning/accountability, work/context, meal planning, appointments/calendar reconciliation, assets/knowledge, travel/hobbies, and evidence-backed automation.

This repository is **intentionally public** portable source. **Mutable operational state** does not belong in the public upstream. Public releases remain gated by the repository's **public-source audit**, privacy checks, tests, and any required live-provider verification.

## The naming model

### MIRROR Layer — reality

MIRROR owns the durable facts and evidence:

- **M**emory and durable state
- **I**ntegrations and authority connections
- **R**eality Record
- **R**econciliation
- **O**bserved evidence
- **R**eliable provenance

In plain English: MIRROR is what the system can prove about your real life, where that fact came from, and which source is authoritative now.

### MIRA Layer — intelligence

MIRA is the default user-facing assistant. MIRA handles:

- conversation;
- reasoning;
- planning;
- recommendations;
- execution through approved tools;
- verification of the result against MIRROR.

MIRA may propose. MIRROR must reconcile reality. A confident chat answer never outranks a live canonical authority.

See [`docs/BRANDING.md`](docs/BRANDING.md) for the naming and compatibility contract.

## Start here if you are not technical

Use [`starter/INSTALL.md`](starter/INSTALL.md).

You do **not** need to know Git, use a terminal, or learn programming to install a personal MIRROR deployment. The installer explains the handful of Git/GitHub words you will see in normal English and keeps the default path in the browser.

The short version is:

1. GitHub stores the rules and change history for your copy of MIRROR.
2. Your day-to-day mutable life data lives in the selected canonical state/evidence authorities, not in GitHub just because GitHub exists.
3. ChatGPT may have read access while Codex or another approved source tool has write access. Those are separate capabilities and must be verified separately.
4. Lasting behavior changes are validated, committed, pushed, and read back when standing write authority exists.

Locked-down or regulated environments use [`starter/ENTERPRISE_PILOT.md`](starter/ENTERPRISE_PILOT.md). ChatGPT, Claude, Microsoft/VA AI environments, Gemini, and other runtimes share the portable policy/data model only where the exact capabilities and approvals are verified.

## State and source architecture

For new-user deployments:

- **Git or managed central source** stores source/version lineage: policy, schemas, migrations, non-secret configuration, enabled features, tests, onboarding, provenance, and custom feature work.
- **Google Sheets or Microsoft Lists/Excel** are starter candidates for structured mutable state when the exact adapter is verified.
- **Google Drive or OneDrive/SharePoint** are retained evidence/document candidates when selected modules need files and write/readback is verified.
- **Google Calendar or Outlook Calendar** may be optional projection/reminder surfaces.
- **Apple/iCloud** participates through browser/mobile use and deliberate import/export unless a verified adapter proves more.
- Another supported database may replace Sheets when explicitly selected.

See `starter/STATE_AUTHORITY_MODEL.md`. `starter/GIT_STATE_MODEL.md` remains only as a compatibility redirect from the short-lived Git-native-state design.

## First boot

After installation, use [`starter/START_HERE.md`](starter/START_HERE.md). First boot:

1. verifies the deployment lane and actual provider capabilities;
2. uses **MIRROR** as the product/platform name and **MIRA** as the default assistant identity unless the owner deliberately customizes a private deployment alias;
3. asks only the bounded kickoff questions;
4. inspects existing capabilities/evidence before asking the user to rebuild history;
5. creates/selects canonical state and evidence authorities;
6. creates an `Authority Registry` and durable `Interview Ledger`;
7. persists source/config/schema changes through the verified source-control lane;
8. continues unresolved interview items across future conversations instead of pretending one setup chat captured a human life perfectly.

**Do not inherit the reference deployment's Google IDs, schedules, aliases, vehicles, tasks, receipts, or mutable state.**

## What MIRROR can organize

The adaptive interview can surface domains the user may not know to request, including briefs and next actions; work and context modes; household/admin; routines and accountability; exercise and study; meal planning and recipes; hobbies and travel; appointments and reminders; orders, receipts, cancellations, replacements and refunds; shopping intent; assets, manuals and verified technical knowledge; reimbursement and optional finance evidence; and actionable email.

Before proposing new connections, first boot follows `starter/CAPABILITY_DISCOVERY.md` and reuses accessible existing systems when possible.

## Reliability rules

- Mutable state lives in canonical authorities, never only chat or Git.
- Important mutations receive provider/state readback before success.
- Use the fewest recurring dispatchers; no hidden retry/child/per-order/per-appointment task fan-out.
- Retry is optional and bounded. Repeated, no-progress, or ambiguous failure trips the **Module Circuit Breaker Report** and stops only the affected module.
- One purchase is one Receipt ID/total; shopping intent, refund, and reimbursement remain distinct.
- People, assets, and retained knowledge use immutable UUID identity where applicable.
- Email sending remains approval-gated.
- CI success never substitutes for live provider readback when provider behavior matters.

## Repository layout

- `starter/` — portable onboarding/distribution boundary
- `starter/INSTALL.md` — browser-only non-technical installer
- `starter/STATE_AUTHORITY_MODEL.md` — mutable-state/evidence authority contract
- `starter/INTERVIEW_LEDGER.md` — durable fail-forward onboarding contract
- `starter/PLATFORM_PORTABILITY.md` — runtime/storage/source portability boundaries
- `starter/ENTERPRISE_PILOT.md` — locked-down and regulated pilot gates
- `starter/features/` — portable feature contracts/manifests
- `skill/ops-brief-policy/` — current reference deployment policy/runtime
- `project/INSTRUCTIONS.md.tmpl` — reference deployment bootstrap
- `scripts/` — validation/source/privacy/bootstrap/fingerprint/import tools
- `tests/` and `starter/tests/` — regression and portable lifecycle tests
- `docs/BRANDING.md` — MIRA/MIRROR naming contract and legacy migration boundary

## Validate

```bash
python3 scripts/validate_repo.py .
python3 scripts/feature_catalog.py --check
python3 scripts/audit_public_source.py . --history
python3 scripts/audit_starter_privacy.py starter
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest discover -s skill/ops-brief-policy/scripts -p 'test_*.py'
python3 starter/tools/validate_feature_manifest.py --check-files
python3 -m unittest discover -s starter/tests -p 'test_*.py'
```

`main` is stable only after repository validation, privacy/source audits, tests, and any required live provider gates pass.
