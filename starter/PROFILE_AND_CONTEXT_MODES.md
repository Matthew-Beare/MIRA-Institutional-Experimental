# Personal Ops Planner Profiles and Context Modes

This contract separates **who the system is helping**, **where/how that person is operating right now**, and **which stock services are active**. Do not collapse these into one giant `mode` flag.

## 1. Per-person life profile

Each primary user/person gets a private mutable profile in the selected canonical structured state authority. A profile may have a user-selected friendly alias, but aliases, family relationships, schedules, appointments, and other personal state never belong in the portable public starter source.

Profiles use **composable roles**, because a person may be both a working parent,
a retired caregiver, or a student who manages a household. Supported roles include:

- `working`
- `self_employed`
- `retired`
- `nonworking`
- `parent_guardian`
- `caregiver`
- `household_manager`
- `student`
- `dependent_minor`
- `custom`

`retired` and `nonworking` are deliberately distinct. `parent_guardian` is a
first-class role, not an alias for caregiver. A dependent minor always has
`dependent_minor` as the primary role and is never flattened into a generic adult
`mixed` profile. Multiple applicable roles otherwise expose `life_profile: mixed`
plus the complete role list and an explicit primary role.

Legacy single-profile labels may still be encountered during migration:

- `working`
- `student`
- `mixed`
- `custom`

These classes route onboarding questions; they are not identities and may change over time.

Retired or nonworking role routing bypasses work-away machinery by default unless
another role or explicit answer makes it relevant. A retiree brief can emphasize
selected appointments, household/admin, family commitments, volunteering,
hobbies, travel, routines, projects, documents, and other enabled domains. A
parent/guardian can emphasize family/school, appointments, household actions and
shopping without forcing work machinery. These are recommendations only; they do
not silently activate services.

The public role label is `Retired`; its optional support template is `Personal Schedule & Wellbeing`.
Never label a user as elderly, infer age/ability/competence,
or infer medication/financial needs from retirement. Appointment reminders and
medication reminders are separate opt-in services. The appointment template may
offer day-before, configured morning-of, and 60-minute relative reminders.
Medication schedules require explicit owner/prescription/pharmacy/clinician
evidence; caregiver sharing is disabled until separately approved.

## 2. Dynamic context mode

Context mode answers a different question: **what environment is the person operating in now?** It is enabled only when that distinction materially changes available tasks, equipment, evidence, notifications, routes, weather, or routines.

Examples:
- `HOME / ROAD`
- `HOME / TRUCK`
- `HOME / FIELD`
- `HOME / CAMPUS`
- `HOME / AWAY`
- user-defined labels

The exact labels are user configuration stored in mutable state. Portable source may recommend labels but must never silently decide a personal context split from a job title alone.

Routing contract:
1. Ask employment/life pattern and exact job title/duties when applicable.
2. Ask whether recurring work/sleep away, rotating sites, field work, vehicle living/working, or another environment split actually occurs.
3. If explicitly no, mark context mode `bypassed` unless the user selects another useful split.
4. If explicitly yes, recommend a mode pair from the duties/environment and ask the user to confirm or rename it.
5. If the role strongly suggests travel/field work but work-away evidence is unresolved, mark `needs_confirmation`; never auto-enable from a title keyword.
6. Driver/trucker/courier/delivery roles normally recommend `HOME / ROAD`, with `HOME / TRUCK` as an alternate when the vehicle itself is the useful boundary.
7. Field-service/rotating-site/overnight roles normally recommend `HOME / FIELD` or `HOME / AWAY`.
8. Student/campus contexts may recommend `HOME / CAMPUS` only when location materially changes work or resources.
9. Explicit user-defined labels outrank recommendations.
10. Context mode never changes the deployment's canonical IANA scheduling timezone.

Departure/return evidence, overrides, task visibility, equipment/connectivity, route/weather behavior, paid work units, and mode-specific routine variants are configured only after the context split is selected.

## 3. Service catalog and activation

The starter catalogues these service domains so a new user can discover them:

- briefs;
- next actions;
- email triage;
- orders and shipments;
- receipt archive;
- finance;
- appointments and Calendar;
- appointment reminders;
- health organization;
- medication reminders;
- shopping;
- recipes and meals;
- household admin;
- routines and fitness;
- education;
- family and school;
- travel;
- work trips;
- assets;
- knowledge;
- recovery;
- skill builder.

Three baseline contracts are introduced early:
- brief/action digest;
- receipt and order lifecycle;
- recipe library/intake.

**Catalogued or stock-provisioned does not mean implemented or silently enabled.**
The router reports `requires_capability_verification` until executable delivery and
dependencies are actually proved. First boot records one explicit activation state
for each service: `enabled`, `disabled`, `unresolved`, `not_applicable`, or
`deferred`. Disabled and not-applicable services are excluded from recommendations.

When enabled:
- Briefs ask for cadence, exact local slot(s), canonical IANA timezone, notification/delivery mode, length, and anti-noise rules.
- Receipt/order lifecycle asks which evidence sources are permitted, update cadence/slot(s), notification behavior, retention, and approval boundaries. It never creates one scheduler job per order.
- Recipe library asks which existing recipe sources should be reconciled/imported and where structured indexes and retained recipe bodies live. Meal planning remains a separate opt-in feature.

A disabled stock service remains available for later activation without reinstalling source.

## 4. AI-use discovery

After the four kickoff questions, onboarding should learn how the person currently uses AI, what work they repeat manually, and what they wish an assistant could remember or coordinate. This is discovery only. Never promise automation that available capabilities cannot actually perform.

## 5. Failure isolation

Profile routing, context routing, briefs, orders, recipes, appointments, and other modules are separate failure domains. Failure of one optional adapter or module must not disable healthy modules. Mutable profile/context/service state remains in its canonical authority; Git stores only the reusable contracts, schemas, tests, and non-secret configuration.

## 6. Verification

Before calling onboarding complete:
- every installed question-bank ID is terminally resolved or explicitly deferred;
- profile class and any private alias are written/read back from canonical state;
- context mode is `bypassed`, explicitly selected, or still visibly unresolved;
- each catalogued service has an explicit activation state;
- any enabled recurring schedule is verified against its canonical IANA timezone and provider readback;
- no personal alias/state leaked into portable source.
