# Life Planner First-Boot Module Catalog

After the four kickoff questions and adaptive `LIFE_INTERVIEW.md`, present modules conversationally in small groups. Recommend a useful default bundle from problems, existing evidence, and available capabilities, then expose adjacent options so the user can discover workflows they did not know to request. Do not silently enable optional modules.

For new-user starter deployments, structured mutable state uses the selected canonical authority, defaulting to Google Sheets, with Google Drive for retained evidence/documents when useful. Git versions policy/config/schema/features/tests. Read `STATE_AUTHORITY_MODEL.md` and `INTERVIEW_LEDGER.md`.

## Core whole-life modules

### Briefs and action digest
Ask: **Do you want a recurring brief combining the few things that changed, need action, or should happen next across enabled life domains?**
Collect cadence, exact local times, canonical timezone, length, priority rules, context differences, and anti-nag rules.

### Weather in briefs
Ask exactly: **Would you like weather included in your briefs?**
Keep it disabled until the user answers. If enabled, collect the selected brief slots, location policy (fixed, manual, verified current, or context-based), units, compact/detail preference, and whether authoritative severe-weather alerts should appear independently. Every weather result needs an explicit location, source, units, and forecast valid time. Stale or unavailable weather degrades only the weather section and never blocks the rest of a brief; a forecast is never presented as an official alert.

### Next-action planner
Ask: **Do you want Life Planner to keep a prioritized next-action queue so you can ask “what should I do next?” without rebuilding context?**
Support deadlines, prerequisites, context/location, available time, user-provided constraints, blocked work, and minimum viable actions. Never infer completion from silence.

### Durable interview completion
The `Interview Ledger` is a required first-boot module. Every question ID remains `Unresolved`, `Asked`, `Answered`, `Resolved from evidence`, `Not applicable`, or `Deferred` until terminally resolved. A conversation detour does not cancel onboarding. Handle the user's current request, then continue the next useful open interview item later.

### Personal accountability and routines
Ask: **Are there recurring habits or routines where useful accountability would help you stay consistent?**
Examples include exercise, mobility/yoga, hiking, household routines, maintenance, creative practice, reading, paperwork, or another commitment. Capture frequency, windows, resources, context variants, minimum viable version, completion definition, miss/reschedule policy, and progression/review rule.

### Education and study coach
Ask: **Do you want help staying accountable for school, certifications, or other learning and deciding what to study next?**
Capture verified deadlines, prerequisites, weekly target, session sizes, source materials, home/away options, offline constraints, accountability cadence, and Calendar preferences. Never fabricate completed work, grades, or attendance.

### Composable life roles, retirement and parent/guardian routing
Ask which roles apply: working, self-employed, retired, nonworking/between jobs, parent/guardian, caregiver, household manager, student, dependent minor, or custom. Retired and nonworking remain distinct. Parent/guardian is first-class and may compose with work, retirement, study, caregiving, or household management. A dependent minor remains primary rather than becoming a generic adult `mixed` profile. Present `Retired` plainly and respectfully with the optional `Personal Schedule & Wellbeing` support template; never infer age, disability, medication, finances, or competence. For retired/nonworking users, surface appointments, household/admin, volunteering, hobbies, travel, family responsibilities, routines, projects, documents, and separately opt-in appointment/medication reminders without forcing work-mode machinery.

### Context modes: HOME / ROAD / TRUCK / FIELD or equivalent
For recurring away/overnight/rotating-site work, offer context modes based on actual duties/environment. For non-travel roles mark HOME/ROAD bypassed unless another context split helps. Driving/trucking is one branch, not the default human condition.

### Existing-system and capability discovery
Ask: **Before we build anything new, what useful information or connected apps do you already have?**
Follow `CAPABILITY_DISCOVERY.md`. Reuse existing authorities/tools when they satisfy the contract. Missing optional integrations block only their dependent paths.

## Food, recreation and planning

### Meal planning and grocery workflow
Ask exactly: **Do you want help with meal planning?**

When enabled:
- reconcile accessible existing recipes/meal plans instead of starting over;
- preserve canonical recipe identity/provenance;
- learn selected preferences, serving pattern, cooking time/equipment, repeat-versus-novelty preference, leftovers/batch/freezer strategy, grocery cadence, and home/away/travel variants;
- store structured recipe indexes, accepted meal plans, pantry/freezer state, meal history, and active shopping intent in the canonical structured authority;
- use Drive for long recipe bodies/images/documents when useful;
- keep meal planning, shopping intent, and purchase history separate;
- never invent dietary/medical restrictions.

### Hobbies, recreation and outdoor planning
Ask: **What do you do for fun, and which parts are annoying to plan or easy to forget?**
For hiking/camping/travel/sports/photography/automotive/crafting or other selected activities, optionally support preparation checklists, equipment, reservations/permits, weather/routes, maintenance/consumables, progression goals, and trip plans.

### Vacation and trip planning
Ask: **Do you want help moving travel ideas from “someday” to an actual plan?**
Support destination research, date constraints, reservations, Calendar projection, packing/preparation, documents, budgets when selected, and context-aware tasks.

## Appointments, Calendar, and communication

### Verified appointment reconciliation
Ask: **Do you want appointment/reservation emails to update your appointment state and Calendar automatically after you approve the rule?**

For each enabled appointment class:
- define allowed evidence/senders, target calendar, reminder profile, tentative/revision/cancellation behavior, confidence threshold, and sensitive-detail policy;
- dedupe by canonical source/appointment identity;
- derive provider type from evidence when possible;
- if provider type is unclear and research is allowed/available, research official clinic/provider pages or reliable public directories;
- use evidence-supported labels such as cardiology, endocrinology, audiology, primary care, dental, etc.; never turn specialty into diagnosis/treatment inference;
- create/update one linked Calendar event;
- apply all configured reminders;
- read the Calendar event back and verify ID, title/type, date/time/timezone, target calendar, reminders, and source linkage;
- write/read back canonical appointment + Calendar Projection state before calling it reconciled;
- revisions/cancellations update the existing appointment/event rather than duplicating it;
- ambiguity asks the user.

Event-specific reminders live in Calendar. Do not create one ChatGPT automation per appointment.

### Reminder profiles
Support defaults globally, per person, and per appointment class. Multiple reminders may include:
- one day before;
- morning-of at a configured local clock time;
- one hour before or another relative interval.

Morning-of intervals are calculated using the event's IANA timezone, not a static UTC offset.

### Medication reminders
Offer medication reminders independently and default them off. An active schedule requires explicit owner, prescription-label, pharmacy, or clinician evidence plus user confirmation. Never infer dose/timing, give missed-dose advice, or share sensitive reminders with a caregiver without explicit opt-in and an exact recipient identity. Project approved reminders through the configured provider and verify readback; do not create one ChatGPT automation per dose.

### Calendar Projection
Ask: **Which verified Life Planner facts, if any, should also appear on Calendar?**
Offer independently appointments/reservations, deliveries, work travel, deadlines, bills/trials, routine/study sessions, maintenance/warranty deadlines, selected tasks, and user-defined types. Revisions update linked events instead of creating duplicates.

### Important-mail triage
Ask which senders/domains and event classes matter. External sends remain approval-gated.

## Orders, purchases and assets

### Orders and shipment lifecycle
Track ordered → shipped → delivered plus revisions, cancellations, replacements, returns, refunds, and stalled shipments through one consolidated lifecycle pipeline.

### Receipt database
Offer searchable purchases from email, files, screenshots, and photos with cross-source dedupe, identifiers, evidence links, line-item relationships, balanced allocations, and unresolved classification only after investigation.

### Shopping and procurement reconciliation
`Shopping & Procurement` is an active shopping list, not purchase history. When durable purchase evidence or explicit owner confirmation satisfies an intent, preserve transaction/reconciliation evidence and **remove the fulfilled shopping row** after verification. A cancellation with no supported replacement leaves it open. Missing product identity becomes a separate reconciliation task rather than a Purchased tombstone.

### Asset acquisition and inventory
Canonical people/physical assets receive immutable UUIDs; friendly names/IDs remain aliases. Search before creating, link exact purchase-line/photo/Gmail evidence, preserve namespaced UPC/GTIN/SKU/part/model/serial identifiers, and enrich supported specs/warranty/compatibility. Receipt and asset views query the same graph in both directions.

### Manuals and reference library
Attempt authoritative manufacturer/OEM manual discovery, retain manuals and references in Drive/evidence storage, and index them in canonical structured state with immutable Knowledge UUID plus explicit related asset/model/part identities. Verified safety-critical specifications require exact applicability, revision and page/section provenance.

## Money, household, and shared state

### Receipt/account financial reconciliation
Connected financial data is evidence. Keep supported expected totals open until settlement/no-settlement resolution and distinguish reimbursement from merchant refund.

### Household, beneficiaries and reimbursements
Support shared responsibility/purchases without duplicating merchant transactions.

### Shared authority
Ask whether a domain should be shared with another person. Support either deliberate sharing of the whole workbook/folder or a scoped shared authority. Explain the visibility boundary and verify access after sharing. Sharing state is separate from sharing a public feature.

## Source lineage and feature exchange

### Personal Git lineage
Every deployment establishes a user-owned Git lineage for source/config/schema/migrations/tests/features and upstream provenance. Routine mutable operational records stay in their canonical state/evidence authorities.

### Share a personal feature
When a customization becomes coherent and passes tests/privacy/source checks, ask exactly: **Do you want to make this feature available to other people?**
If yes, sanitize configuration/state, use synthetic fixtures, declare dependencies/permissions, version the feature, show the contribution diff, and send it upstream only under explicit publication authority.

## First-boot recommendation behavior

Recommend a small bundle based on stated problems, existing evidence, and verified dependencies. Explain adjacent capabilities. The Interview Ledger continues across conversation detours until every applicable question is resolved.
