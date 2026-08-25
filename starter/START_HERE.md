# Life Planner First Boot — Start Here

Start after browser-only verification in [`INSTALL.md`](INSTALL.md) and [`PROVIDER_ONBOARDING.md`](PROVIDER_ONBOARDING.md). A non-technical user never uses local developer tools.

`questions.json` is the core question bank. `questions.profile-and-stock-services.json` extends it. Every installed question-bank ID uses the same durable Interview Ledger.

## Copy/paste first-boot prompt

```text
Help me set up my own Life Planner as an inheritable whole-life organizer. Discover useful workflows I may not know to request, inspect what I already use before asking me to reconnect things, and build the smallest system that materially improves my life.

Conversation rules:
- Treat INSTALL.md as a prerequisite. Read back its lane fields before provisioning; never substitute local tools, a fork, Codespaces, credentials, personal accounts, or unapproved services.
- Ask no more than four related questions at a time.
- Begin with exactly these four kickoff questions:
  1. What should the system be called?
  2. What IANA timezone is permanently authoritative for scheduled routines, including while I travel?
  3. What do I do with most of my week? Include whether I am working, retired, studying, caregiving, or something else; if working, include job title/duties/schedule/work-away pattern.
  4. What are the biggest things I want help remembering, organizing, deciding, planning, or following through on?
- After those four, early in discovery ask how I currently use AI and what repetitive remembering, organizing, researching, deciding, or follow-through I wish an assistant handled better. Suggest only automations supported by real capabilities and permissions.
- Never inherit another deployment's timezone, schedules, accounts, assets, routines, goals, IDs, configuration, aliases, or state.
- After kickoff, inspect available capabilities/evidence before asking me to recreate information.
- Use INTERVIEW_LEDGER.md. Every installed question-bank ID must eventually be Answered, Resolved from evidence, or Not applicable. Deferred/Unresolved questions remain open.
- If I take the conversation somewhere else, answer that request first, update anything it incidentally resolves, then return to the next useful interview question at the end when reasonable. Do not restart the interview and do not silently abandon it.
- A preference/permission question is never inferred from evidence.

State and source:
- Personal/organization Git or managed central source is my versioned lineage for code, policy, schemas, migrations, non-secret configuration, features, tests, onboarding, and recovery.
- Mutable life state uses the selected canonical state authority. Personal defaults are Google Sheets/Google Drive; approved Microsoft 365 candidates are Lists/Excel and OneDrive/SharePoint. Apple/iCloud is manual import/export unless a verified adapter proves otherwise.
- First boot creates an Authority Registry and Interview Ledger in the structured state authority.
- Do not put routine mutable recipes, appointments, routines, meal history, shopping rows, receipts, aliases, or medical-event scheduling into Git just to version them.
- Google Calendar is an optional projection/reminder surface, not the sole state database.
- A supported database may replace Sheets when deliberately selected.
- Sharing a state authority with another person is explicit. Support whole-authority sharing or a separate scoped shared workbook/folder. Never assume family access.
- When standing source write is allowed, lasting behavior/config/schema changes automatically update validation, commit, and push, then receive remote readback. A read connector never proves write. Managed-source users use approved change control. Routine state writes verify against the selected authority.
- When a coherent custom feature passes tests/privacy checks, ask exactly: `Do you want to make this feature available to other people?` Never publish private state automatically.

Capability/evidence discovery:
- Before asking me to connect an app, inspect relevant tools/connectors/plugins already available when possible.
- Use PROVIDER_ONBOARDING.md and PLATFORM_PORTABILITY.md: Google, Microsoft 365/OneDrive, Apple/iCloud/manual, ChatGPT, Claude, Microsoft/VA AI, Gemini and other lanes have no assumed feature parity. Regulated-sensitive data requires current approval evidence.
- Reuse accessible current conversation, uploaded/File Library material, Drive/Sheets/Calendar/email, and other connected evidence rather than making me rebuild history.
- If useful prior-chat material is inaccessible, explain an ingestion path instead of pretending it was read. A fresh conversation must recover from canonical authorities even after old chats are deleted.
- Optional integrations fail only their dependent path.

Profiles and context modes:
- Keep a per-person life profile separate from dynamic context. A private friendly alias may be stored in mutable state but never embedded in portable source.
- Use composable roles: working, self-employed, retired, nonworking, parent/guardian, caregiver, household manager, student, dependent minor, or custom. Retirement differs from nonworking; parent/guardian is first-class; a dependent minor remains primary.
- Retired/nonworking roles bypass work-away machinery by default. Parent/guardian routing may surface family/school, appointments, household actions and shopping without activating them.
- If work/sleep away is not recurring, mark HOME/ROAD bypassed unless another context split helps.
- If recurring, interview exact job title/duties, departure/return evidence, work/sleep rhythm, connectivity/equipment, home-only versus away-capable work, and paid work units when relevant.
- Driving/trucking, courier, and delivery roles normally recommend HOME/ROAD, with HOME/TRUCK as an alternate. Field/rotating-site work may recommend HOME/FIELD or HOME/AWAY. Campus-dependent study may use HOME/CAMPUS. Recommendations require user confirmation or renaming.
- A title that merely suggests travel produces `needs_confirmation`; never silently enable a mode from a keyword.
- Context never changes canonical scheduling time.

Stock-provisioned services:
- The starter includes brief/action-digest, receipt/order lifecycle, and recipe-library contracts by default. Stock-provisioned does not mean silently enabled.
- The catalog also exposes next actions, email, finance, appointments, health organization, shopping, household, routines, education, family/school, travel/work trips, assets, knowledge, recovery, and skill building.
- Record each as enabled, disabled, unresolved, not applicable, or deferred. Capability verification—not catalog presence—establishes implementation.
- Read each selected feature manifest's `delivery_status` before describing availability. `contract-only` is not executable delivery and must be disclosed plainly.
- If briefs are enabled, ask cadence, slots, timezone, delivery, length, priority/anti-noise rules, and exactly: `Would you like weather included in your briefs?`
- If receipt/order lifecycle is enabled, ask permitted evidence sources, reconciliation cadence/slots, notification behavior, retention, and approval boundaries. Never create one automation per order.
- If recipe library is enabled, reconcile accessible existing recipes and ask which sources/state/evidence stores to use. Meal planning remains separately optional.

Meal planning:
- Explicitly ask: `Do you want help with meal planning?`
- If yes, offer recipe organization, grocery intent, pantry/freezer/leftover awareness, batch cooking, home/away/travel/camping food, and cost/waste reduction.
- Search accessible chats/files/File Library/Drive/notes and connected evidence for existing recipes/meal plans before starting over.
- Store structured recipe indexes/plans/pantry/shopping state in the selected structured state authority; store long recipe bodies/images/docs in Drive when useful.
- Shopping intent is an active shopping list and remains distinct from purchase history.

Appointments and reminders:
- Ask whether I want appointments/reservations or medical-event scheduling tracked and which appointment classes may reconcile automatically from email.
- For each candidate, read complete evidence, dedupe against canonical appointment/source identity, and ask on conflict/low confidence.
- Determine appointment type and provider type from the evidence when possible. If provider type is unclear and research is allowed/available, research official or reliable public sources; never infer diagnosis/treatment from specialty.
- Let me configure reminder profiles globally, per appointment class, or per person. Support day-before, a configured morning-of local clock time, and a relative reminder such as one hour before.
- Create/update one linked Calendar event when enabled, read it back, and verify ID, title/type, date/time/timezone, target calendar, reminders, and source linkage.
- Then write/read back canonical appointment + Calendar Projection state. Only then mark reconciliation complete.
- Revisions/cancellations update the same appointment/event. Do not create one ChatGPT automation per appointment.

Canonical scheduler clock:
- Ask for exact local times in one canonical IANA timezone. At runtime use `now.astimezone(ZoneInfo(canonical_tz))`; never use device/travel timezone or a fixed UTC offset.
- Verify recurrence, local time/TZID, timing mode, notifications, duplicates, and an actual firing/Run Log; trust provider metadata only when its provider contract defines the field.

Minimum Useful Setup:
- Authority Registry + Interview Ledger + per-person profile;
- stock-provisioned brief/action digest, receipt/order lifecycle, and recipe-library services, each explicitly enabled/disabled/unresolved;
- context-mode router, explicitly selected or bypassed;
- next-action planner when useful;
- accountability for selected routines/study/projects/household/hobbies/travel/goals;
- meal planning when selected;
- appointment/email reconciliation and Calendar Projection when selected;
- active shopping, assets/manuals, money reconciliation, and knowledge when useful;
- people, physical assets, and retained knowledge use immutable UUID identity where applicable.

Orders/purchases:
- One Receipt ID = one underlying transaction/total.
- Preserve ordered/shipped/delivered/exception/cancellation requested/partial cancellation/confirmed cancellation/returned/refunded history. A true replacement gets its own linked Receipt ID.
- Shopping & Procurement is an active shopping list. Fulfilled intent disappears only after durable purchase/owner-confirmation evidence is preserved and verified.
- Keep supported expected charges Awaiting Settlement until matched, split-matched, no-settlement, or otherwise resolved.

Module Circuit Breaker Report:
- Retry is optional/bounded. No blind retries for deterministic validation, permission/auth, ambiguous writes, CI loops, or scheduler mismatch.
- On repeated/no-progress/ambiguous failure, stop that module, read back/preserve known-good state, continue healthy modules, and report trigger, preserved state, blocked operation, and one specific next action.

Email/contact:
- Never send email automatically.
- Show recipient/channel, subject, and complete body, then ask exactly `Do you want me to send this email?`

Initial provisioning:
- Show one concise dependency/resource/state summary and obtain explicit approval for the initial write bundle.
- Create/verify the structured state authority, selected evidence root, Authority Registry, Interview Ledger, per-person profile, stock-service activation state, context routing state, and source deployment configuration.
- Run applicable CI, starter privacy, and public-source audit gates before scheduled/provider writes.

Start now by asking only the four kickoff questions.
```
