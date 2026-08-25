# Historical Feature Audit — 2026-08-22

**Status: superseded. Do not use this file as current production state, release readiness, scheduler health, repository visibility, or operational evidence.**

This file originally captured a point-in-time integration audit while multiple development branches were being reconciled. That format became unsafe because it mixed durable release observations with mutable runtime facts such as active trips, mileage, task state and provider conditions. Mutable operational state belongs only in the canonical live authorities, never in Git.

## What remains historically useful

The 2026-08-22 review identified the major feature families that required integration and regression coverage:

- brief scheduling and Run Log behavior;
- context-aware HOME/ROAD operation;
- mileage/pay isolation and terminal-pair knowledge;
- complete Gmail/order/shipment reconciliation;
- receipt identity, cancellation, replacement, refund and allocation semantics;
- first-boot onboarding and dependency gates;
- private Git recovery/versioning;
- reusable starter/privacy boundaries;
- finance/reimbursement separation;
- future knowledge, inventory and self-hosting work.

Those requirements are now enforced, when implemented, by the canonical skill, current documentation, validator/tests and live authorities. Historical branch labels or `LIVE`/`GAP` statements in the old audit are not authoritative today.

## Current release-readiness sources

Use these instead of this historical snapshot:

1. `skill/ops-brief-policy/SKILL.md` and its references for durable policy.
2. `project/POLICY_FINGERPRINT.txt` for canonical policy-source integrity.
3. `scripts/validate_repo.py` plus executable tests for repository contracts.
4. `starter/START_HERE.md`, `starter/DEPENDENCIES.md`, `starter/LIFE_INTERVIEW.md` and starter tests for first boot.
5. GitHub provider metadata for actual repository visibility and branch/CI state. A prose claim that a repository is private is never sufficient.
6. The live canonical Sheets/Drive/Gmail/Calendar/Finances authorities for mutable operational facts.
7. The automation provider plus canonical Run Log for actual scheduled execution. VEVENT text or travel-local metadata alone does not prove scheduler health.

## Release gate

A new-user deployment is not ready merely because repository CI is green. Before first boot is handed to a real user, also require:

- an actually private target deployment repository verified from provider metadata;
- a sanitized starter source that does not inherit production repository history or mutable state;
- dependency read/write verification for the modules being enabled;
- schedule/notification/duplicate readback for any Scheduled Tasks;
- an observed canonical-time firing before declaring a scheduler repair cleared;
- a clean-account or equivalently isolated first-boot smoke test before stable release status.

No active Trip ID, mileage occurrence, receipt row, user account detail, repository-visibility claim, automation last-run time, or other mutable production fact should be added back to this historical file.