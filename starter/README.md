# MIRROR First-Boot Starter

This reusable onboarding kit builds a new user's **MIRROR** deployment without copying the reference deployment's mutable state. **MIRA** is the default assistant identity.

The non-technical human entry point is [`INSTALL.md`](INSTALL.md). It is deliberately browser-only and explains Git/GitHub in plain language before asking the user to touch anything. [`START_HERE.md`](START_HERE.md) begins only after deployment-lane capability verification.

## What the names mean

- **MIRROR Layer**: memory/state, integrations, Reality Record, reconciliation, observed evidence, and provenance.
- **MIRA Layer**: conversation, reasoning, planning, recommendations, approved execution, and verification back into MIRROR.

A user may choose a private nickname, but the upstream product remains MIRROR and the default assistant remains MIRA. See [`../docs/BRANDING.md`](../docs/BRANDING.md).

## Public distribution boundary

`starter/` is the portable surface of the public upstream. The personal default uses GitHub's browser template flow to create a private user-owned repository from the audited default branch. Enterprise users may use approved organization Git or managed central source without personal Git accounts. Local Git is developer-only and never a non-technical fallback.

Git carries portable behavior, schemas, migrations, configuration, tests, onboarding, and feature lineage. Mutable personal records stay in selected state/evidence authorities.

The supported starter candidates are:

1. Google Sheets or Microsoft Lists/Excel for structured mutable state;
2. Google Drive or OneDrive/SharePoint for retained evidence/documents when useful;
3. personal/organization Git or managed central source for source/version lineage;
4. Google Calendar or Outlook Calendar as an optional projection/reminder surface;
5. other integrations only when selected modules need them.

Apple/iCloud is supported through browser/mobile use and manual import/export unless a verified adapter proves more. ChatGPT, Claude, Microsoft/VA AI environments, Gemini, and other runtimes use the portable core only after exact capabilities are observed. Read `PLATFORM_PORTABILITY.md` and `ENTERPRISE_PILOT.md`.

## Durable interview

First boot creates an `Interview Ledger` in canonical structured state. Every question ID in `questions.json` remains tracked until it is `Answered`, `Resolved from evidence`, or `Not applicable`. `Deferred` and `Unresolved` remain open.

If the user changes subjects, MIRA answers the immediate request first, records any incidental answers, and later resumes the next useful unresolved interview item. The point is to survive normal human topic-jumping without quietly dropping half the setup.

## Built-in discovery

First boot can discover/configure, when useful:

- concise briefs and prioritized next actions;
- working, self-employed, retired, nonworking, parent/guardian, caregiver, household-manager, student, dependent, and custom roles;
- accountability/routines and exercise with optional wearable evidence;
- household routines and pickup/drop-off reminders without per-chore task sprawl;
- education/study planning and context-aware variants;
- work/context modes for travel/overnight/field roles;
- meal planning, recipes, grocery intent, leftovers/pantry/freezer workflows;
- hobbies, outdoor preparation, vacations, and trip planning;
- appointments/reservations with verified evidence and Calendar reconciliation;
- separately opt-in medication reminders from explicit supported schedules;
- orders, receipts, shopping, cancellation/replacement/refund/payment reconciliation;
- assets, manuals, technical knowledge, reimbursement, and optional finance workflows;
- capability/plugin discovery so existing connected tools are reused before redundant setup is requested;
- explicit personal/household/scoped state sharing.

Accounts, exact schedules, taxonomy, authority IDs, repository visibility, and selected features are never inherited from the reference deployment.

## First-boot workflow

1. Complete `INSTALL.md` and verify the exact runtime/source/state/evidence capabilities.
2. Record the observed upstream commit/provenance.
3. Apply the MIRA/MIRROR identity contract from `../docs/BRANDING.md`.
4. Ask only the kickoff questions in `START_HERE.md`.
5. Discover existing capabilities/evidence before creating duplicates.
6. Create/select the structured state authority and evidence root.
7. Create the `Authority Registry` and `Interview Ledger`.
8. Conduct `LIFE_INTERVIEW.md` in small related batches, using evidence and branch logic where appropriate.
9. Recommend a Minimum Useful Setup and adjacent capabilities the user may not know to request.
10. Verify only dependencies required by selected modules; optional connector failures are module-scoped.
11. Obtain bounded provisioning approval and create/verify state/evidence resources.
12. Generate, validate, commit, push, and read back source changes when the source lane has standing write authorization.
13. Continue unresolved Interview Ledger items across later conversations until coverage is complete.
14. Never treat green CI as proof of live scheduler/provider behavior without required readback or observed execution.

## Boundaries

- Never inherit another user's timezone, schedule, accounts, assets, receipts, authority IDs, or mutable records.
- Never route a non-technical onboarding user to Command Prompt, PowerShell, Terminal, local Git, GitHub CLI, Codespaces, tokens, or SSH keys.
- Never create a personal account or external connector to bypass organization policy.
- Never infer runtime feature parity or regulated-data approval from a product name.
- Never treat a read-only GitHub connection as proof of source write capability.
- Never claim arbitrary old chats are globally searchable.
- Never create one automation per order, appointment, routine, or assignment when Calendar/consolidated dispatch can handle it.
- Never request or commit passwords, tokens, keys, full card data, private message/receipt bodies, account exports, medical records, school submissions, or mutable operational exports to portable Git.
- Automatic Git push does not imply merge, release, publication, force-push, or visibility-change authority.
- Completion comes from the user or reliable connected evidence, never silence.

See `STATE_AUTHORITY_MODEL.md`, `INTERVIEW_LEDGER.md`, `VERSIONING.md`, `PERSONAL_FORK_LIFECYCLE.md`, `CAPABILITY_DISCOVERY.md`, `PLATFORM_PORTABILITY.md`, `ENTERPRISE_PILOT.md`, and `DEPENDENCIES.md`.
