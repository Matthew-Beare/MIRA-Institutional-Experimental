# Personal Ops Planner First-Boot Dependencies

First boot verifies every selected dependency before claiming a module is installed. Missing access blocks only the dependent module. Before asking the user to connect anything, read `CAPABILITY_DISCOVERY.md` and inspect already available tools/connectors/plugins when the platform permits it. Never ask a non-technical user for passwords, access tokens, OAuth secrets, private keys, or full payment-card numbers.

## Dependency-minimization rule

Default new-user architecture:

- **Approved AI runtime:** ChatGPT, Claude, an organization-approved Microsoft/VA AI, Gemini, or another runtime only to the extent its observed capabilities satisfy the module contract.
- **Git or managed central source:** required durable source/version lineage for code/policy/schema/config/features/tests; a corporate end user does not need a personal Git account when administrators own the source.
- **Google Sheets, Microsoft Lists/Excel, or another selected database:** structured mutable state authority resources.
- **Google Drive, OneDrive/SharePoint, or deliberate manual file exchange:** evidence/document authority when selected modules need retained files.
- **Google Calendar, Outlook Calendar, or another verified calendar:** optional projection/reminder surface.
- Gmail, finance, fitness/wearable, maps/weather/travel, and other integrations are optional module adapters.

A supported database may replace Sheets when deliberately selected. Do not require both Sheets and another database as simultaneous writable masters for the same data class.

Prefer one canonical authority per data class, module-scoped failure domains, adapters around optional capabilities, one consolidated scheduler per purpose/cadence, Calendar events for event-specific reminders, and write/readback verification at every module boundary.

## Machine-readable module dependency contract

Every portable feature manifest uses manifest contract v3 and declares a `delivery_status` plus a `runtime_contract` containing:

- `contract-only` means the repository contains a reviewed contract but no claim of executable delivery;
- `implemented` requires at least one script entrypoint and executable test entry, so Markdown contract prose cannot masquerade as runtime verification;

- `failure_domain`;
- `required_capabilities`;
- `optional_capabilities`;
- `conditional_capabilities`;
- `canonical_state_classes`;
- `idempotency_scope`;
- `on_required_failure`;
- `on_optional_failure`;
- `cross_module_writes`.

Rules:

1. baseline required capabilities are the smallest set needed for the module to function at all;
2. optional capabilities may not also be baseline required;
3. conditional capabilities must already be declared optional and become required only for the selected sub-path described by the rule;
4. required-capability failure is `block-module-only`;
5. optional-capability failure is `degrade-capability-and-continue`;
6. direct cross-module writes default to none;
7. any deliberate cross-module mutation must be declared, use stable IDs, and receive readback at both authority boundaries;
8. feature-to-feature dependencies must resolve inside the install bundle and form an acyclic graph;
9. CI validates referenced live-feature files actually exist, so a manifest cannot advertise a script/schema/test that vanished.

The manifest is the install/runtime dependency contract. Prose may explain it but cannot weaken it.

## Failure-domain mapping

The Authority Registry records which physical provider resource owns each data class and the failure domain that resource participates in.

Recommended production boundaries are described in `STATE_AUTHORITY_MODEL.md`. In particular, commerce/receipts and mileage/pay should not be collapsed into an unrelated core-ops resource merely for convenience. Other domains may share a resource only when the coupling is intentional and accepted.

If one authority resource fails, only modules mapped to that authority or explicitly dependent on it are blocked. If one provider suffers a platform-wide outage, multiple modules may become blocked together; that is a provider infrastructure failure, not permission to create a shadow database.

## Integration health

Persist an Integration Registry or equivalent with module ID, capability ID, required/optional/conditional role, provider/resource, failure domain, health, circuit state, last verification, and next action.

Health meanings:

- `Healthy` — required contract verified;
- `Degraded` — baseline module can run but an optional/conditional path is unavailable;
- `Blocked` — a baseline required capability is unavailable;
- `Unknown` — not yet verified.

A module evaluates its own contract and health. It does not treat an unrelated module's success as proof that its dependencies work.

## Git or managed repository — required source lineage

Git stores durable policy, schemas, tests, migrations, onboarding, selected-module configuration, authority references, feature manifests/runtime contracts, and portable/personal feature code. Routine mutable operational records do **not** live in Git.

A deployment repository may be public or private by explicit owner choice and policy. It may be personal GitHub, approved GitHub Enterprise/GitLab/Azure Repos, or a managed central repository that users consume without their own Git accounts. Public source requires the public-source audit and must not contain secrets, credentials, mutable operational exports, message/receipt bodies, financial account data, medical records, school submissions, or unintended personal information.

### Upstream lifecycle

1. for a non-technical user, create one private repository from the audited public GitHub template using `INSTALL.md`; never substitute a local command line, Codespace, token, or SSH key;
   an enterprise user may instead use approved organization Git or a pinned managed central release under `ENTERPRISE_PILOT.md`;
2. record observed upstream provenance;
3. verify source read, source write and remote readback independently for the selected AI/runtime and source mode; the ordinary ChatGPT GitHub app is read-only, and a Claude/GitHub or other readable connection is not assumed writable;
4. generate non-secret deployment config, schema/migrations, feature lock, authority references/failure domains, and policy;
5. validate the complete feature dependency graph and referenced files;
6. validate, commit/push, and read back the coherent first-boot source checkpoint;
7. after standing Git authorization, lasting behavior/config/schema/feature changes automatically validate, commit, push, and verify remote state.

Automatic Git versioning does not imply force-push, visibility change, release, merge, or public contribution authority.

## Structured state authorities — required per selected stateful module

Default personal provider: Google Sheets. Microsoft 365 deployments may use Microsoft Lists or explicit Excel tables in OneDrive/SharePoint. Another database is allowed only when its adapter satisfies the same stable-ID, read/write/dedupe/audit/readback contract.

First boot creates/selects and verifies each structured authority needed by selected modules before that module begins state-changing automation. Read `STATE_AUTHORITY_MODEL.md`.

At minimum the core deployment can provision:
- `Authority Registry`;
- `Interview Ledger`;
- `Integration Registry`;
- module-specific canonical tables/schemas.

Every state mutation is read → dedupe/correlate → verify module dependencies → write → readback → verify. If the authority is unavailable, stop that module and report `Action Required — <authority> unavailable` rather than substituting chat or Git. Unrelated modules with independent healthy authorities continue.

## Recovery snapshots

A recovery snapshot is optional but recommended for production state authorities. Provider version history, exports, or immutable/timestamped snapshots may be used for disaster recovery, but a snapshot is never a second live writable authority and is never silently promoted after an outage.

Restoration requires an explicit recovery transaction, validation, and provider readback. This avoids split-brain state while still giving recoverability.

## Evidence store

Google Drive is the personal default. Microsoft 365 may use OneDrive or a SharePoint document library. Use stable provider file IDs/links from canonical state rows. Do not create an evidence store merely because it exists if the deployment has no retained-file use case.

Typical classes include receipts, manuals/reference, recipe bodies/images, administrative documents, and other bulky originals.

An evidence-provider failure blocks retained-file operations that require it; it does not automatically block state-only operations whose runtime contract does not require retained files.

Apple/iCloud supports browser or Files-app import/export in the portable manual lane. Do not claim general automated access to a user's iCloud Drive; CloudKit app-container access is not an arbitrary iCloud Drive adapter.

## AI runtimes and connector parity

Read `PLATFORM_PORTABILITY.md` and `platform-capabilities.json`. ChatGPT, Claude, Microsoft Copilot/VA GPT, Gemini and MCP-capable runtimes may all carry the portable core, but their tools are not interchangeable. Verify every required capability with the exact workspace/tenant identity.

For `regulated-sensitive` data, the exact AI deployment, storage, purpose and connector actions require current organization approval. A reachable public service or personal account is never a fallback for blocked enterprise policy.

## Shared authorities

First boot asks whether any domain should be shared with another person.

Support either:
- explicit provider sharing of an existing workbook/folder; or
- a separate scoped shared workbook/folder for household, meal planning, travel, projects, etc.

Record the scope/grant and failure domain in the Authority Registry and verify provider read/write access after sharing. Never infer family access.

## Capability discovery before connection prompts

Inspect relevant already-available capabilities before telling the user to connect another service. Reuse a verified existing connector when it satisfies the module contract. If a selected workflow needs an unavailable capability, search supported plugins/apps when possible and explain the permission boundary.

Never invent a Garmin, finance, calendar, email, or other connection merely because a workflow would be nicer with one.

## Gmail / email

Optional evidence adapter for selected appointment, receipt/order, actionable-mail, school/admin, or document workflows. Verify bounded full-message read capability for the relevant class. Label/archive writes are separate. Sending remains approval-gated.

### Appointment reconciliation

For approved appointment-email automation:
- email supplies evidence;
- the structured appointment authority owns canonical appointment/reconciliation state;
- Calendar is an optional/conditional projection/reminder surface;
- public provider research may enrich provider specialty/type when evidence is unclear and research is allowed.

A Gmail failure blocks email-driven reconciliation, not manual appointment management or unrelated modules.

## Google Calendar

Optional projection/reminder adapter. Verify read access first. After approval, verify bounded create/update and read it back.

For each projected appointment verify event ID, target calendar, title/type, date/time/timezone, reminder policy, and canonical source linkage. Revisions update the same linked event.

Support multiple reminders, including day-before, a configured morning-of local clock time, and relative reminders such as one hour before. Fixed local-clock reminders must be converted using the event's IANA timezone, not a static offset.

Event-specific reminders live in Calendar rather than generating one ChatGPT task per appointment.

## Fitness / wearable / activity integrations

Optional evidence adapters. If a relevant connector/plugin is already available, offer it for selected exercise/accountability workflows. Verify what fields it exposes. Use only user-selected supported metrics.

A wearable connection must never become a prerequisite for basic exercise planning, and activity data must not be treated as diagnosis/injury evidence.

## Financial accounts

Optional evidence adapter for account-level charge/refund/cash-flow reconciliation. Use the product's account-linking flow; never request banking credentials in chat. Inspect coverage/freshness before conclusions.

## Maps, weather, and travel capabilities

Optional current-input adapters for hiking, outdoor, route, vacation, or trip planning. Keep planning usable without them.

## Scheduled Tasks and canonical timezone integrity

Scheduled Tasks are optional unless the user wants recurring briefs/digests/accountability/condition watches.

Treat scheduling as an evidence chain:
1. canonical VEVENT/RRULE/TZID/local time;
2. exactly the intended enabled dispatcher, correct timing mode, no duplicate;
3. expected notification state;
4. runtime canonical-clock gate;
5. subsequent actual firing/Run Log.

The runtime canonical-clock gate converts the current instant to the configured IANA timezone, e.g. `now.astimezone(ZoneInfo(canonical_timezone))`, then compares that local clock to the intended slot. Never compare against travel/device timezone or a manual UTC offset. This naturally handles DST.

A field called `default_timezone` is authoritative only when the provider contract explicitly defines it as persistent task execution state.

Keep the fewest dispatchers necessary. Do not create per-order, per-appointment, or hidden retry tasks. A scheduler failure blocks that dispatcher/module family; it does not justify rewriting unrelated module schedules.

## Existing chats, files, and File Library

Use current conversation and accessible uploaded/File Library material when relevant. Do not claim global search over arbitrary old ChatGPT conversations.

If useful prior-chat material is inaccessible, ask the user to open/share/export it or move durable content into the selected canonical authority. Once ingested, the old chat should not remain the sole authority.

## Dependency gate output

Before provisioning, summarize each selected module and dependency as failure domain, required/optional/conditional role, existing/available capability, read verified / write verified / missing / partial, exact next action, and whether unrelated onboarding can continue.
