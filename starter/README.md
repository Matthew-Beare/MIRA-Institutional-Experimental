# Generic Personal Ops Planner First-Boot Starter

This reusable onboarding kit builds a new user's Personal Ops Planner without copying the reference deployment's mutable state. The non-technical human entry point is [`INSTALL.md`](INSTALL.md); [`START_HERE.md`](START_HERE.md) begins only after deployment-lane capability verification.

## Public distribution boundary

`starter/` is the portable surface of the public upstream. The personal default uses GitHub's browser template flow to create a private user-owned repository from the audited default branch. Enterprise users may use approved organization Git or managed central source without personal Git accounts. Local Git is developer-only and never a non-technical fallback. Git carries portable behavior, schemas, migrations, configuration, tests, onboarding, and feature lineage. Mutable personal records stay in selected state/evidence authorities.

The supported starter candidates are:

1. Google Sheets or Microsoft Lists/Excel for structured mutable state;
2. Google Drive or OneDrive/SharePoint for retained evidence/documents when useful;
3. personal/organization Git or managed central source for source/version lineage;
4. Google Calendar or Outlook Calendar as an optional projection/reminder surface;
5. other integrations only when selected modules need them.

Apple/iCloud is supported through browser/mobile use and manual import/export; no general automated iCloud Drive adapter is claimed. ChatGPT, Claude, Microsoft/VA AI environments, Gemini and other runtimes use the portable core only after exact capabilities are observed. Read `PLATFORM_PORTABILITY.md` and `ENTERPRISE_PILOT.md`.

A supported database may replace Sheets when deliberately selected. Read `STATE_AUTHORITY_MODEL.md`.

## Durable interview

First boot creates an `Interview Ledger` in canonical structured state. Every question ID in `questions.json` remains tracked until it is `Answered`, `Resolved from evidence`, or `Not applicable`. `Deferred` and `Unresolved` remain open.

If the user changes subjects, Personal Ops Planner answers the immediate request first, records any incidental answers, and later resumes the next useful unresolved interview item. This is defined in `INTERVIEW_LEDGER.md` and prevents a lively human conversation from quietly deleting half the setup process.

## Built-in discovery and capabilities

First boot can discover/configure, when useful:

- concise briefs and prioritized next actions;
- composable working, self-employed, retired, nonworking, parent/guardian, caregiver, household-manager, student, dependent and custom roles, including a respectful `Personal Schedule & Wellbeing` retired support template;
- personal accountability/routines and exercise with optional wearable evidence;
- household routines and pickup/drop-off reminders, including multi-stage laundry, without per-chore Scheduled Task sprawl;
- education/study planning and home/away variants;
- work/context modes for travel/overnight/field roles;
- **meal planning**, recipes, grocery intent, leftovers/pantry/freezer workflows;
- hobbies, hiking/outdoor preparation, vacations, and trip planning;
- appointments/reservations with provider-type enrichment, day-before/morning-of/relative reminders, and verified evidence → Calendar reconciliation;
- separately opt-in medication reminders from explicit supported schedules, with no dose inference or automatic caregiver sharing;
- orders/receipts/shopping/payment reconciliation;
- assets/manuals/knowledge, household/reimbursements, and optional finance workflows;
- capability/plugin discovery so existing connected tools are reused before redundant setup is requested;
- deliberate personal/household/scoped state sharing.

Accounts, exact schedules, taxonomy, authority IDs, repository visibility, and selected features are never inherited from the reference deployment.

## First-boot workflow

1. Complete `INSTALL.md`: select personal, enterprise-managed, or portable-manual lane; verify the exact AI runtime, data classification, source, state and evidence capabilities. Personal ChatGPT/Codex users use the GitHub template/read/write path.
2. Record the observed upstream commit/provenance; never infer it from a local copy.
3. Ask only the four kickoff questions in `START_HERE.md`.
4. Discover existing capabilities/evidence before creating duplicate systems.
5. Create/select the structured state authority and evidence root.
6. Create the `Authority Registry` and `Interview Ledger`.
7. Conduct `LIFE_INTERVIEW.md` in batches of at most four related questions, using evidence and branch logic to resolve questions when appropriate.
8. Recommend a Minimum Useful Setup and adjacent capabilities the user may not know to request.
9. Verify only dependencies required by selected modules; optional connector failures are module-scoped.
10. Obtain bounded provisioning approval and create/verify state/evidence resources.
11. Generate/validate/commit/push the user's source configuration, schemas/migrations, feature lock, and policy, or route it through the approved managed-source change process.
12. Continue unresolved Interview Ledger items across later conversations until coverage is complete.
13. Never treat green CI as proof of live scheduler/provider behavior without required readback/observed execution.

## Meal planning storage

Structured recipe metadata, meal plans, pantry/freezer facts, meal history, and active shopping intent live in the canonical structured authority. Long recipe bodies/images/documents may live in Drive with stable links. Existing accessible recipe material is reconciled before asking the user to rebuild it.

## Appointment storage and reminders

Canonical appointment state lives in the structured state authority. Email is evidence and Calendar is projection/reminders. If provider type is not explicit, approved public research may identify an evidence-supported specialty such as cardiology, endocrinology, audiology, primary care, dental, etc. Specialty never implies diagnosis/treatment.

Reminder profiles can combine day-before, configured morning-of local time, and relative intervals such as one hour before. Local-clock calculations use the event's IANA timezone.

Medication reminders default off. An active schedule requires explicit owner, prescription-label, pharmacy, or clinician evidence plus confirmation. Never infer dose/timing, give missed-dose advice, or share with a caregiver without separate exact-recipient approval.

## Canonical-time scheduling

Recurring dispatchers use their configured IANA timezone as authority. Runtime checks convert the current instant into the canonical timezone and compare the canonical local clock with the intended slot. Travel/device timezone and hard-coded UTC offsets never move the routine.

## Personal development and sharing

Recommended source branches:
- `main` for known-good deployment source;
- optional `experimental` for several concurrent experiments;
- `feature/*` and `fix/*` for bounded work.

After standing Git authorization, lasting source behavior/config/schema changes automatically validate, commit, push, and receive remote readback. Routine mutable state updates go to canonical state authorities instead.

When a coherent personal feature passes tests/privacy/source checks, ask exactly: `Do you want to make this feature available to other people?` A yes starts sanitized upstream contribution preparation. State sharing with another person is a separate explicit authority-sharing operation.

## Boundaries

- Never inherit another user's timezone, schedule, accounts, assets, receipts, authority IDs, or mutable records.
- Never route a non-technical onboarding user to Command Prompt, PowerShell, Terminal, local Git, GitHub CLI, Codespaces, tokens, or SSH keys.
- Never create a personal account or external connector to bypass organization policy.
- Never infer AI-runtime feature parity or regulated-data approval from a product name.
- Never treat the read-only ChatGPT GitHub app as proof of Codex write capability.
- Never claim arbitrary old ChatGPT conversations are globally searchable.
- Never create one automation per order, appointment, routine, or assignment when Calendar/consolidated dispatch can handle it.
- Never request/commit passwords, tokens, keys, full card data, private message/receipt bodies, account exports, medical records, school submissions, or mutable operational exports to portable Git.
- Automatic Git push does not imply merge/release/publication/force-push authority.
- Completion comes from the user or reliable connected evidence, never silence.

See `STATE_AUTHORITY_MODEL.md`, `INTERVIEW_LEDGER.md`, `VERSIONING.md`, `PERSONAL_FORK_LIFECYCLE.md`, `CAPABILITY_DISCOVERY.md`, `PLATFORM_PORTABILITY.md`, `ENTERPRISE_PILOT.md`, and `DEPENDENCIES.md`.
