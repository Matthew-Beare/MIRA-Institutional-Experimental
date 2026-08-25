# MIRA | M.I.R.R.O.R. First-Boot Starter

**M.I.R.R.O.R.** means **Memory, Integration, Reality, Reconciliation, Observation, and Record**. **MIRA** is the **MIRROR Intelligence and Reasoning Assistant**. This starter builds a new user's M.I.R.R.O.R. reality layer with MIRA as the default assistant, without copying another deployment's mutable state.

M.I.R.R.O.R. **holds the durable reflection of reality**. With user-approved integrations, that reflection can connect assets, finances, calendars, email, orders and receipts, appointments, tasks, medication reminder schedules, documents and knowledge, travel/work context, meals, and new custom domains.

Start with [`QUICK_START.md`](QUICK_START.md). It is the default non-technical browser path. [`INSTALL.md`](INSTALL.md) is the detailed capability/troubleshooting reference, and [`START_HERE.md`](START_HERE.md) is the deeper interview contract.

The former **Life Planner** name and the `life-planner` skill/package path remain compatibility identifiers during migration.

## What goes where

- **Git or approved managed source**: policy, schemas, migrations, tests, onboarding, non-secret configuration, reusable features, and version lineage.
- **Google Sheets / Microsoft Lists or Excel / another approved structured provider**: mutable personal records and canonical structured state.
- **Google Drive / OneDrive or SharePoint / another approved evidence store**: retained evidence and documents where useful.
- **Calendar**: optional projection and reminders, not automatically the sole state database.

Git is not the default database for mutable personal records.

## Default identity

M.I.R.R.O.R. is the system. MIRA is the assistant.

First boot must not make a non-technical user invent those names. A private assistant alias can be chosen later and stored as mutable profile state without renaming upstream.

## Durable interview

First boot creates an `Authority Registry` and an `Interview Ledger` in canonical structured state. Questions stay open until they are answered, resolved from evidence, not applicable, or explicitly deferred. A conversational detour does not silently abandon onboarding.

## Built-in discovery

The starter can discover and configure, when useful:

- briefs and next actions;
- work, study, household, retirement, caregiving, and family contexts;
- meal planning, recipes, groceries, pantry/freezer, and leftovers;
- appointments and reminders;
- orders, receipts, shopping, refunds, and payment reconciliation;
- assets, manuals, identifiers, specifications, warranties, and maintenance;
- travel/work context modes and mileage;
- optional finance and medication-reminder workflows;
- actionable email and retained knowledge; and
- reusable custom skills and features.

Existing connected evidence should be inspected before asking the user to rebuild information manually.

## Create and share a skill

A user can describe a recurring problem to MIRA in ordinary language. MIRA should inspect existing capabilities, design the behavior and data boundaries, implement it on a feature branch, add tests and synthetic fixtures, verify it, and commit a coherent checkpoint.

Personal skills stay private by default. When a skill is coherent, MIRA asks exactly: **Do you want to make this feature available to other people?** A yes starts the sanitization and public-contribution gate; it does not itself publish anything.

See [`SHARED_FEATURE_WORKFLOW.md`](SHARED_FEATURE_WORKFLOW.md).

## Safe upgrades and user-owned features

Every installed feature has durable ownership and lineage in `features.lock.json`. `feature-dependency-map.json` records its feature and capability dependencies and is regenerated/checked whenever feature source changes. CI fails if a feature is added or changed without updating that map.

Upstream updates never replace a user's repository wholesale. MIRA compares the originally adopted upstream state, the user's current state, and the candidate release. User-owned and locally modified behavior is preserved by default. The plain-language update screen explains what the user has, what would change, what dependency is missing if anything, and offers **keep mine**, **use the new version**, or **show more detail**. Nothing changes until the user approves it.

Before any approved change MIRA creates a rollback checkpoint and reminds the user they can return to the previous working setup. AI may recommend consolidation when a local feature overlaps a new upstream feature, but it may not delete or replace local behavior without explicit user approval and full regression validation.

See [`FEATURE_RECONCILIATION.md`](FEATURE_RECONCILIATION.md).

## Same code across release channels

M.I.R.R.O.R. Personal-Production, Personal-Experimental, and Institutional-Experimental are all public onboarding repositories using the same portable application code from one canonical source revision. Channel-specific feature forks are forbidden. Only deployment policy, approved provider/runtime configuration, data classification, and external mutable state differ.

## Boundaries

Never inherit another deployment's accounts, IDs, timezone, schedules, assets, receipts, tasks, or mutable records. Never treat ChatGPT GitHub read access as proof of Codex write access. Never send email automatically. Never claim a provider write before readback.

The `life-planner` package name is retained until a bounded compatibility migration proves every dependent path and test.
