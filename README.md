# Personal Ops Planner / Daily Ops Brief

Personal Ops Planner is a version-controlled personal-operations framework for briefs, persistent state, receipts/orders, planning/accountability, work/context, meal planning, appointments/calendar reconciliation, assets/knowledge, travel/hobbies, and evidence-backed automation.

This repository is **intentionally public**. It is the stable upstream plus a public reference deployment. Mutable operational state does not belong in portable Git source.

## State and source architecture

For new-user starter deployments:

- **Git or managed central source** is source/version lineage: policy, schemas, migrations, non-secret configuration, enabled features, tests, onboarding, provenance, and custom feature work.
- **Google Sheets or Microsoft Lists/Excel** are supported starter candidates for structured mutable state when the exact adapter is verified.
- **Google Drive or OneDrive/SharePoint** are supported retained evidence/document candidates when selected modules need files and write/readback is verified.
- **Google Calendar or Outlook Calendar** may be optional projection/reminder surfaces.
- **Apple/iCloud** participates through browser/mobile use and deliberate import/export; general automated iCloud Drive access is not claimed.
- Another supported database may replace Sheets when explicitly selected.

The current Daily Ops reference deployment already follows this external-authority model with its configured Sheets/Drive authorities.

See `starter/STATE_AUTHORITY_MODEL.md`. `starter/GIT_STATE_MODEL.md` is retained only as a compatibility redirect from the short-lived Git-native-state design.

## Start here as a new user

Use [`starter/INSTALL.md`](starter/INSTALL.md). It is the browser-only path for a non-technical user and must be completed before [`starter/START_HERE.md`](starter/START_HERE.md). The normal personal lifecycle is:

1. use GitHub's web template flow once to create a private user-controlled repository from the audited public starter;
2. connect that exact repository to the read-only ChatGPT GitHub app and separately to write-capable Codex;
3. verify repository owner, visibility, default branch, commit, read access, and write access without a local command line;
4. run adaptive first boot;
5. inspect existing capabilities/evidence before asking the user to recreate information;
6. create/select the structured state authority and Drive evidence root;
7. create an `Authority Registry` and durable `Interview Ledger`;
8. generate schemas/migrations/configuration/feature lock/policy in Git;
9. verify state-authority writes and Git source checkpoint independently;
10. continue unresolved interview items across future conversations instead of assuming one perfect setup chat;
11. evolve custom behavior on feature branches;
12. when a feature becomes reusable, ask whether the user wants to contribute a sanitized portable version upstream.

Locked-down and regulated environments use [`starter/ENTERPRISE_PILOT.md`](starter/ENTERPRISE_PILOT.md). They may use approved organization Git or a managed central release so end users do not need personal Git accounts. ChatGPT, Claude, Microsoft/VA AI environments, Gemini and other runtimes share the portable policy/data core but have **no assumed feature parity**; see [`starter/PLATFORM_PORTABILITY.md`](starter/PLATFORM_PORTABILITY.md).

**Do not inherit the reference deployment's Google IDs, schedules, aliases, vehicles, tasks, receipts, or mutable state.**

## Fail-forward onboarding

The interview is tracked in canonical state, not merely remembered in chat. Each question ID becomes one of:

`Unresolved` · `Asked` · `Answered` · `Resolved from evidence` · `Not applicable` · `Deferred`

Setup is complete only when every applicable question is resolved. A user may change topics freely: Personal Ops Planner handles the immediate request, records any incidental answers, then resumes the next useful open interview item later. Evidence can resolve factual questions; preferences/permissions cannot be silently inferred.

See `starter/INTERVIEW_LEDGER.md`.

## Inherit → customize → improve → share

```text
public Personal Ops Planner template
        ↓ browser template copy
user Git source lineage + selected state authorities
        ↓ personal customization
feature/* + optional experimental integration
        ↓ tested personal feature
        ↓ "Do you want to make this feature available to other people?"
sanitation + synthetic fixtures + CI
        ↓
public upstream PR
```

Sharing a **feature** is different from sharing **state**. A deployment may explicitly share a whole Google authority or a scoped shared workbook/folder with another person. That is recorded and verified separately from public Git contribution.

## What Personal Ops Planner can organize

The adaptive interview can surface domains the user may not know to request, including:

- briefs and prioritized next actions;
- composable working, self-employed, retired, nonworking, parent/guardian, caregiver, household-manager, student, dependent and custom roles; the respectful retired support template is `Personal Schedule & Wellbeing` and never infers age or ability;
- tasks, projects, household/admin, and recurring accountability;
- exercise/fitness/hiking with optional supported wearable/activity evidence;
- school/study planning and context-aware coaching;
- meal planning, recipes, pantry/freezer/leftovers, grocery intent, and cost/waste workflows;
- hobbies, hiking/outdoor preparation, vacations/trip planning, and travel logistics;
- appointments/reservations with verified evidence → Calendar reconciliation plus opt-in day-before, morning-of and relative reminders;
- opt-in medication reminders from explicit owner/prescription/pharmacy/clinician schedules, with no dose inference or automatic caregiver sharing;
- orders, receipts, cancellations, replacements, refunds, and active shopping intent;
- assets, namespaced UPC/GTIN/SKU/part/model/serial identities, bidirectional receipt links, manuals/reference knowledge, verified specifications, warranties, and maintenance;
- household/reimbursement and optional finance evidence;
- actionable email and durable reference material.

Before proposing new connections, first boot follows `starter/CAPABILITY_DISCOVERY.md` and reuses accessible existing systems when possible.

## Meal planning

First boot explicitly asks `Do you want help with meal planning?` If selected, existing accessible recipes/meal plans are reconciled before starting over. Structured recipe indexes, accepted plans, pantry/freezer state, meal history, and shopping intent live in the canonical structured state authority. Long recipe bodies/images/documents may live in Drive with stable links.

## Appointments and reminders

Appointment reconciliation can:

1. read complete evidence;
2. dedupe against canonical appointment/source state;
3. identify provider type from evidence;
4. if still unclear and research is allowed, research the provider using official/reliable public sources;
5. create/update one linked Calendar event;
6. apply a configured reminder profile;
7. read the Calendar event back;
8. write/read back canonical appointment + Calendar Projection state;
9. only then mark the source reconciled.

Supported organizational labels can include cardiology, endocrinology, audiology, primary care, dental, etc. Specialty is never treated as diagnosis/treatment evidence.

Reminder profiles may include multiple reminders such as day-before, a configured morning-of local clock time, and one hour before. Calendar owns event-specific reminders rather than spawning one ChatGPT Scheduled Task per appointment.

Medication reminders are independent and default off. An active regimen schedule must be explicitly confirmed from owner, prescription-label, pharmacy, or clinician evidence. Personal Ops Planner does not infer dose/timing, advise on missed doses, or share with a caregiver without explicit scope and recipient approval.

## Receipt-linked assets and technical knowledge

One normalized graph connects exact receipt lines, immutable asset/vehicle/tool UUIDs, explicit assignment/installation/use relationships, evidence objects, namespaced identifiers, retained manuals, and technical specifications. Receipt Browser and Asset Browser query that graph from either direction. General ownership edges are excluded from traversal so a vehicle query does not pull in every household asset.

Photo/OCR/barcode extraction is candidate evidence, not automatic truth. UPC/GTIN values retain leading zeroes and pass check-digit validation; merchant SKU, manufacturer part/model and serial values retain their namespace. Retained manuals require canonical Drive readback. Verified safety-critical torque, tire-pressure, fluid, alignment and load specifications require authoritative source tier, exact applicability, revision, and page/section provenance.

## Canonical scheduler clock

Recurring dispatchers use a canonical IANA timezone. The production executable captures its own system UTC instant, converts it into that timezone, and compares the canonical local clock with the intended slot. It never accepts a model-guessed production timestamp or depends on travel/device timezone or a hand-maintained UTC offset.

For example, the same summer PM instant displays as 2:45 Eastern, 1:45 Central, 12:45 Mountain, and 11:45 Pacific. The dispatcher still asks whether `America/New_York` is 14:45 at that instant. IANA timezone rules handle DST.

## Dependency design

Use the fewest authorities necessary:

- one canonical mutable authority per data class;
- a verified evidence store only when retained files/evidence are useful;
- personal/organization Git or managed central source for durable source/versioning;
- optional integrations as module-scoped adapters;
- one consolidated scheduler per purpose/cadence;
- Calendar events for event-specific reminders;
- write/readback verification at every authority boundary.

## Repository layout

- `starter/` — portable onboarding/distribution boundary
- `starter/STATE_AUTHORITY_MODEL.md` — mutable-state/evidence authority contract
- `starter/INTERVIEW_LEDGER.md` — durable fail-forward onboarding contract
- `starter/PLATFORM_PORTABILITY.md` — AI/storage/source portability and honest capability boundaries
- `starter/ENTERPRISE_PILOT.md` — browser-only locked-down and regulated pilot gates
- `starter/platform-capabilities.json` — machine-readable runtime/storage/source candidates and claim rules
- `starter/features/` — portable feature contracts/manifests
- `skill/ops-brief-policy/` — current reference deployment policy/runtime
- `project/INSTRUCTIONS.md.tmpl` — reference deployment bootstrap
- `scripts/` — validation/source/privacy/bootstrap/fingerprint/import tools
- `tests/` and `starter/tests/` — regression and portable lifecycle tests
- `docs/feature-ledger-2026-08-24.md` — project-conversation feature inventory with requirement and implementation status kept separate
- `docs/feature-catalog.json` and `docs/feature-catalog.md` — generated hierarchical catalog; CI rejects drift and requires code/test evidence paths for integrated claims
- `docs/code-inventory.json` — one bounded responsibility, separation rationale, and direct test suite for every production Python file; unlisted code fails CI
- `docs/beta-hardening-audit-2026-08-24.md` — root cause, failure matrix, code justification, and release blockers
- `docs/onboarding-hardening-audit-2026-08-25.md` — Foodie failure root cause, browser-only repair, capability gates, and remaining live template gate
- `docs/platform-portability-audit-2026-08-25.md` — Google/Microsoft/Apple/AI/enterprise portability audit and remaining live gates
- `docs/BRANDING.md` — public working name, per-user naming, and legacy-identifier migration boundary

## Validate

```bash
python3 scripts/validate_repo.py .
python3 scripts/feature_catalog.py --check
python3 scripts/audit_public_source.py . --history
python3 scripts/audit_starter_privacy.py starter
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest discover -s skill/ops-brief-policy/scripts -p 'test_*.py'
python3 starter/tools/validate_feature_manifest.py
python3 -m unittest discover -s starter/tests -p 'test_*.py'
```

## Reliability rules

- Mutable state lives in canonical authorities, never only chat/Git.
- Important mutations receive provider/state readback before success.
- Use the fewest recurring dispatchers; no hidden retry/child/per-order/per-appointment task fan-out.
- Retry is optional/bounded. Repeated/no-progress/ambiguous failure trips the **Module Circuit Breaker Report** and stops only the affected module.
- One purchase is one Receipt ID/total; shopping intent, refund, and reimbursement remain distinct.
- People/assets/retained knowledge use immutable UUID identity.
- Email sending remains approval-gated.
- CI success never substitutes for live provider readback when provider behavior matters.

`main` is the stable public upstream only after repository validation, public-source audit, starter privacy audit, deterministic/runtime tests, portable feature/starter tests, and merge authority pass.
