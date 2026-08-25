# Locked-down and regulated enterprise pilot

This lane is for corporate, government, health-care, education, and other managed devices where the end user may have no installation rights and external services may be blocked.

## Absolute boundary

Do not create a personal cloud account, personal Git repository, external connector, forwarding rule, or shadow database to work around organizational controls. A website being reachable does not make it approved.

For `regulated-sensitive` data, onboarding is blocked until the organization confirms the exact:

- AI product/deployment and authenticated identity;
- approved data classifications and purposes;
- storage tenant, folder/list/site, and sharing scope;
- connector/app and least-privilege actions;
- source-control/change-management route;
- retention, records, audit, and incident rules.

No password, token, code, credential, patient/client record, or sensitive source content is collected merely to test connectivity.

## Browser-only lanes

1. **Organization-managed full lane:** approved AI + approved Microsoft 365/Google Workspace resources + approved organization Git or managed central source.
2. **Managed-source lane:** the user consumes an administrator-maintained release and stores mutable state in approved tenant resources; personal policy changes use an approved change request.
3. **Non-sensitive demonstration lane:** synthetic or public data only; no production connector writes and no claim of organizational approval.
4. **Portable manual lane:** approved browser plus user-mediated import/export; no unattended automation claim.

The system remains usable on Windows, macOS, ChromeOS, iPhone/iPad, Android, and other browser-capable devices because default onboarding requires no local Git, shell, package installation, or administrator rights. Provider access may still be blocked by tenant/network policy.

## Pilot sequence

### Gate 0 — sponsor and use case

Record the accountable sponsor, intended users, exact problem, forbidden data, success criteria, and review date. Keep the first scope narrow enough to inspect manually.

### Gate 1 — synthetic demonstration

Use synthetic or public data to demonstrate interview continuity, task/brief structure, policy portability, and export formats. Do not connect production mail, calendars, drives, or repositories.

### Gate 2 — approved read-only discovery

With the organization-approved identity, inspect only the approved runtime, source release, storage candidate, and connector capabilities. Record `available`, `blocked`, or `unknown`; a provider name is not proof.

### Gate 3 — bounded write proof

Use one disposable pilot record/file in an approved pilot location:

`read → bounded write → readback → verify exact ID/content → remove or retain under the approved policy`

Do not test by writing to a real operational, clinical, personnel, financial, or production record.

### Gate 4 — module acceptance

Enable one module at a time. Verify its required capabilities, failure-domain behavior, audit/provenance fields, permission denial behavior, and human review. Optional adapter failure must not take down unrelated modules.

### Gate 5 — scheduling

Only if the approved AI/runtime exposes scheduling: verify the canonical IANA timezone, recurrence, notification state, duplicate count, runtime clock gate, and one observed firing/Run Log. Otherwise use the organization's approved scheduler or operate manually; do not fake parity.

### Gate 6 — change and rollback

Pin the approved release. Record the organization Git or managed central source route, test updates with non-sensitive fixtures, and document rollback. End users without Git access remain valid users; they simply cannot bypass managed change control.

## VA-specific deployment gate

Current VA guidance must be rechecked at enrollment because approvals can change. As of July 22, 2026, VA's public guidance identifies Microsoft Copilot Chat and VA GPT as broadly available VA-identity tools approved for VA-sensitive data; Claude for Gov, ChatGPT FedRAMP, Microsoft Copilot Studio, and Summit's AI Assistant are gated approved options. GitHub Copilot is listed for coding but not for VA-sensitive data.

That dated list is **not** blanket authorization for this project, arbitrary connectors, personal accounts, every facility, or every data class. The pilot sponsor must confirm the exact tool, ATO-covered purpose, identity, storage, and connector actions before sensitive data enters the workflow. Public ChatGPT, Claude, or Gemini accounts remain a synthetic/non-sensitive lane unless VA explicitly authorizes that exact deployment and use.

Primary source: [VA Guidance for Generative AI Use](https://department.va.gov/ai/guidance-for-generative-ai-use-at-va/).

## Acceptance evidence

A production-capable enterprise lane requires all of the following:

- sponsor and current approval-evidence reference (a boolean is insufficient);
- exact runtime/deployment/identity readback;
- exact data-classification boundary;
- approved source mode and pinned release;
- canonical state read/write/readback proof;
- evidence-store read/write/readback proof when selected;
- module-scoped permission/failure tests;
- no personal-account workaround;
- human review and audit/provenance output;
- scheduler observed firing when scheduling is selected.

Anything missing is reported as blocked or degraded with one concrete next action. It is never renamed “installed.”
