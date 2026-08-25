# Capability and Existing-Evidence Discovery

First boot should discover what is already available before asking a user to rebuild their life manually or connect redundant services. Mutable M.I.R.R.O.R. state lives in the selected canonical structured authority, normally Google Sheets or Microsoft Lists/Excel; Google Drive or OneDrive/SharePoint may retain selected evidence/documents; Git or a managed central source versions behavior/config/schema/features.

Load `platform-capabilities.json` and use `tools/provider_capability_router.py` for the portable onboarding baseline. For runtime behavior readiness and integration suggestions, combine `behavior-dependencies.json`, the deployment Integration Registry, `integration-workflow-catalog.json`, and `tools/integration_dependency_router.py`. The human never runs a command. Provider names are labels only: no AI, storage, source-control, finance, wearable, email, calendar, or scheduler capability is accepted without observed access and the required readback/proof.

## Discovery order

1. **Environment and data classification:** personal, enterprise, or regulated; public/personal/non-sensitive-work/regulated-sensitive; exact organization approval when required.
2. **AI runtime/deployment:** record ChatGPT, Claude, organization-approved Microsoft/VA AI, Gemini, or another runtime plus exact workspace/tenant and available tools.
3. **Current deployment source/config:** verify personal/organization Git lineage or a pinned managed central release, installed feature/schema versions, and authority references.
4. **Canonical state/evidence authorities:** inspect the selected Sheets/database/Lists/Excel and Drive/OneDrive/SharePoint roots so existing state is not duplicated.
5. **Current conversation and supplied files:** use facts/evidence already present.
6. **File Library / uploaded material:** search relevant existing files before requesting re-entry.
7. **Connected apps/tools/connectors:** use a supported runtime enumeration when one exists; otherwise use the existing Integration Registry plus bounded relevant provider/tool probes. Never claim a complete plugin scan if the runtime cannot enumerate everything.
8. **Verify capabilities separately from connection state:** record what an integration advertises, then verify only the reads, writes, scopes, history coverage, notification paths, or readbacks the selected behavior actually needs.
9. **Existing external systems:** detect calendars, email, finance sources, wearables, recipe collections, task apps, etc. that may contain useful evidence.
10. **Available plugins/apps:** when a selected workflow needs an unavailable capability, search supported integrations before declaring it impossible or giving a manual workaround.
11. **User interview:** ask only for information evidence cannot resolve or that requires preference/consent.
12. **Goal-matched workflow review:** compare verified capabilities with explicit active goals and offer a small number of high-value workflows without enabling anything silently.

Do not claim global access to arbitrary old ChatGPT conversations or arbitrary connected plugins. If useful prior-chat content is inaccessible, ask the user to open/share/export it or move durable content into the selected canonical authority. If global plugin enumeration is unavailable, say so internally and use the Integration Registry rather than inventing a complete list. The old chat should not remain the sole database.

## Integration Registry

The Integration Registry is the deployment-owned record of observed integrations and current capability evidence. It should distinguish:

- provider/integration display name;
- connection state: connected, disconnected, unknown, or blocked;
- advertised capabilities;
- verified capabilities;
- selected authorities that the integration backs; and
- any provider-specific health/readback evidence retained by the deployment.

A connection badge is not proof. Only `verified_capabilities` feed behavior dependency readiness. When a connection changes, refresh the registry and recalculate readiness; do not rewrite the durable behavior dependency map simply because the user's account state changed.

`integration-registry.example.json` shows the portable shape. Real provider IDs, account identifiers, tokens, private records, and other mutable user state remain outside portable source.

## Capability map

Build a setup-time capability map such as:

| Capability | Example use | Role | Gate |
|---|---|---|---|
| AI runtime approval | safe execution for the selected data class | execution boundary | exact deployment/identity/purpose/data-class approval |
| Git or managed source | source/config/features/versioning | source authority | pinned release; bounded write + remote readback when personal changes are allowed |
| Sheets/Lists/Excel/database | tasks, interview ledger, appointments, meal plans, recipes index | canonical mutable state | read/write + row/object readback |
| Drive/OneDrive/SharePoint/files | receipt/manual/recipe/document bodies | evidence/document authority | read first; bounded write + provider readback after approval |
| Gmail/email | appointment/order/receipt/admin evidence | evidence adapter | bounded full-message read when selected |
| Calendar | appointment/event projection + reminders | projection/reminder adapter | read first; create/update/readback after approval |
| Financial data | transaction evidence | evidence adapter | exact account scope, history coverage/freshness, read-only unless a distinct action is approved |
| Fitness/activity integration | exercise evidence/progression | evidence adapter | supported user-selected metrics only |
| Barcode/QR scanner | asset/inventory identifier intake | evidence/input adapter | decode exact symbology/value; corroborate product identity before canonical write |
| Maps/weather/travel tools | trip/vacation planning inputs | current-input adapter | use only when relevant |
| Notification/device path | reminder delivery | projection adapter | prove the selected device/path can receive the intended alert modality |
| Other plugin/app | domain-specific workflow | optional adapter | inspect permissions/dependencies first |

The capability map is setup reasoning. Persist durable selected capability/authority configuration in approved Git/managed source and mutable integration health in the Authority/Integration Registries. Credentials remain with providers. On regulated systems, never create a personal account or external connector to replace a blocked organization capability.

## Existing-workflow import

For each selected domain ask: **Do you already have a system, plan, list, library, history, or connected app for this?**

When yes:
- inspect reachable evidence first;
- identify the existing authority/data quality;
- dedupe before import;
- preserve provenance;
- migrate only what is useful;
- write approved structured state to the selected canonical authority and retained files to Drive/evidence storage;
- do not create a second authoritative database by default.

This is especially important for recipes/meal plans, exercise history, calendars, school documents, projects, assets, receipts, and existing customizations.

## Fitness and wearable sources

If a fitness/wearable/activity connector is already available, verify the exact readable metrics before treating `wearable_read` as present. Do not assume Garmin or another brand exists merely because wearable support is possible. Use only metrics the user selects. Never infer diagnoses, injury status, or unsafe progression.

A recommendation requires both verified wearable data and an explicit active goal. For example, if the registry actually identifies a Garmin smartwatch and the user has already stated a fitness goal, MIRA may offer to use activity data as optional evidence for routines/accountability. The connection itself does not create the fitness goal and does not enable the workflow.

## Financial integration sources

A connected bank/card/finance provider can contribute `finance_read` only after the relevant account scope and history coverage are verified. Match it to explicit goals such as budgeting, saving, spending review, debt planning, subscription review, or transaction reconciliation. Never infer a financial goal from the mere existence of an account, and never treat positive/negative transaction signs or transfer rows as income without the finance subsystem's own reconciliation rules.

## Appointment/provider enrichment

If appointment evidence identifies a provider but not the provider type/specialty, and public research is allowed/available, search official provider/clinic pages or reliable public directories before asking the user. Store only an evidence-supported organizational label such as cardiology, endocrinology, audiology, primary care, dental, etc. If unresolved, ask. Specialty is not a diagnosis.

## Discovery should create bounded recommendations

Examples:
- frequent missed appointments + verified Gmail + verified Calendar + explicit reminder goal → offer appointment reconciliation and reminder profiles;
- existing recipes + grocery friction → offer meal planning and shopping-intent integration;
- recurring hiking + Calendar/maps/weather → offer hike/trip preparation and vacation planning;
- travel-heavy job + limited away connectivity → offer context modes and offline-preparation workflows;
- explicit exercise goal + verified activity connector → offer evidence-backed accountability/progression;
- explicit saving goal + verified finance read → offer spending/reconciliation support;
- asset/inventory goal + barcode scanner + web research/evidence store → offer scan-to-identify/manual-link workflow;
- retired user + appointment/admin load → offer appointments, renewals, documents, and reminders without forcing a work model.

Use `integration-workflow-catalog.json` to cap the review at five suggestions. Do not repeatedly re-offer workflows the user has dismissed unless their goals or requested review state materially change.

## Missing dependency setup

When dependency preflight finds a required capability or authority missing for a feature the user wants:

1. explain the missing dependency and affected feature in plain language;
2. state that unrelated features still work and nothing changes automatically;
3. ask **Do you need help setting this up?**;
4. if yes, give no more than five visible steps, prefer an already connected suitable integration, and request the minimum necessary access;
5. after the user acts, perform the capability-specific verification/readback, update the Integration Registry, and rerun only the affected dependency branch;
6. if the user declines, leave the feature blocked and say they can return when the dependency is ready.

Do not mark a dependency satisfied based on the user's statement that an app is "connected" when the required action can be verified directly.

## Dependency minimization

Every module declares the smallest dependency set it needs. A missing optional connector is section-scoped and must not break unrelated modules.

Prefer:
- one canonical structured authority per mutable data class;
- one durable Git or managed central lineage for source/config;
- Drive/OneDrive/SharePoint or another approved evidence store only for retained files that benefit from it;
- one consolidated scheduler dispatcher per cadence/purpose;
- Calendar events for event-specific reminders rather than one ChatGPT task per appointment;
- adapters around optional integrations rather than cross-module direct coupling;
- readback/verification at each authority boundary.
