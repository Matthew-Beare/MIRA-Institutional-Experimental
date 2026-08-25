# Capability and Existing-Evidence Discovery

First boot should discover what is already available before asking a user to rebuild their life manually or connect redundant services. Mutable Personal Ops Planner state lives in the selected canonical structured authority, normally Google Sheets or Microsoft Lists/Excel; Google Drive or OneDrive/SharePoint may retain selected evidence/documents; Git or a managed central source versions behavior/config/schema/features.

Load `platform-capabilities.json` and use `tools/provider_capability_router.py` from the assistant runtime. The human never runs a command. Provider names are labels only: no AI, storage, source-control or scheduler capability is accepted without observed access and the required readback.

## Discovery order

1. **Environment and data classification:** personal, enterprise, or regulated; public/personal/non-sensitive-work/regulated-sensitive; exact organization approval when required.
2. **AI runtime/deployment:** record ChatGPT, Claude, organization-approved Microsoft/VA AI, Gemini, or another runtime plus exact workspace/tenant and available tools.
3. **Current deployment source/config:** verify personal/organization Git lineage or a pinned managed central release, installed feature/schema versions, and authority references.
4. **Canonical state/evidence authorities:** inspect the selected Sheets/database/Lists/Excel and Drive/OneDrive/SharePoint roots so existing state is not duplicated.
5. **Current conversation and supplied files:** use facts/evidence already present.
6. **File Library / uploaded material:** search relevant existing files before requesting re-entry.
7. **Connected apps/tools/connectors:** inspect available capabilities and perform harmless bounded reads only when relevant.
8. **Existing external systems:** detect calendars, email, finance sources, wearables, recipe collections, task apps, etc. that may contain useful evidence.
9. **Available plugins/apps:** when a selected workflow needs an unavailable capability, search supported integrations before declaring it impossible or giving a manual workaround.
10. **User interview:** ask only for information evidence cannot resolve or that requires preference/consent.

Do not claim global access to arbitrary old ChatGPT conversations. If useful prior-chat content is inaccessible, ask the user to open/share/export it or move durable content into the selected canonical authority. The old chat should not remain the sole database.

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
| Financial data | transaction evidence | evidence adapter | account coverage/freshness check |
| Fitness/activity integration | exercise evidence/progression | evidence adapter | supported user-selected metrics only |
| Maps/weather/travel tools | trip/vacation planning inputs | current-input adapter | use only when relevant |
| Other plugin/app | domain-specific workflow | optional adapter | inspect permissions/dependencies first |

The capability map is setup reasoning. Persist durable selected capability/authority configuration in approved Git/managed source and the Authority Registry. Credentials remain with providers. On regulated systems, never create a personal account or external connector to replace a blocked organization capability.

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

If a fitness/wearable/activity connector is already available, offer it as optional evidence for selected routines. Do not assume Garmin or another brand exists. Verify supported fields and use only metrics the user selects. Never infer diagnoses, injury status, or unsafe progression.

## Appointment/provider enrichment

If appointment evidence identifies a provider but not the provider type/specialty, and public research is allowed/available, search official provider/clinic pages or reliable public directories before asking the user. Store only an evidence-supported organizational label such as cardiology, endocrinology, audiology, primary care, dental, etc. If unresolved, ask. Specialty is not a diagnosis.

## Discovery should create recommendations

Examples:
- frequent missed appointments + Gmail + Calendar → offer verified appointment reconciliation and reminder profiles;
- existing recipes + grocery friction → offer meal planning and shopping-intent integration;
- recurring hiking + Calendar/maps/weather → offer hike/trip preparation and vacation planning;
- travel-heavy job + limited away connectivity → offer context modes and offline-preparation workflows;
- exercise goal + activity connector → offer evidence-backed accountability/progression;
- retired user + appointment/admin load → offer appointments, renewals, documents, and reminders without forcing a work model.

The system should reveal adjacent useful options without enabling them silently.

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
