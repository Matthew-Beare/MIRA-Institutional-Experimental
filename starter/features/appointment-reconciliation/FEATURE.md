# Appointment Reconciliation

## Purpose

Turn user-approved classes of appointment/reservation evidence into one verified canonical appointment in the selected structured state authority and optional linked projections, then reconcile later revisions/cancellations without duplicates.

Manual appointment tracking works with the canonical state authority alone. Email, Calendar, public provider research, and native spoken-notification delivery are optional adapters.

## Enablement

First boot captures:
- whether appointment/reservation and/or medical-event scheduling help is wanted;
- eligible evidence sources/senders/domains;
- target calendar when projection is enabled;
- canonical timezone and reminder profiles;
- tentative-date handling;
- revision/cancellation policy;
- confidence threshold and ambiguity behavior;
- minimum-detail policy for sensitive appointment classes;
- preferred appointment-type/specialty labels;
- whether public provider research may be used to resolve provider type;
- whether spoken reminders are wanted and whether generic or title-level speech is allowed;
- attendee/invitation policy.

## Provider identity / specialty enrichment

Provider resolution is **cache first, research second**. Use `../../appointment-identity-contract.json` and `../../tools/appointment_identity.py` as the portable identity contract/reference implementation.

For each new candidate:

1. search the durable provider/person directory by source binding, known alias and contact identifiers;
2. reuse an existing verified entity UUID/category without repeating public research;
3. only when unresolved and research is permitted/available, search the provider/clinic/person name plus location when known;
4. prefer **official clinic/provider pages**, health-system directories, or another reliable professional directory;
5. record the evidence URL/source and confidence;
6. if evidence conflicts or remains unclear, ask instead of guessing.

Provider specialty/category is an organizational fact, not diagnosis/treatment evidence. Never infer why the user is seeing a specialist.

When the owner corrects an identity or label, treat that correction as durable evidence. Bind the observed source/name alias to the corrected entity and use it in future appointments so the same mistake does not trigger repeated research.

## Reminder profiles

Support multiple reminder rules globally, per person, and/or per appointment class, including:

- one calendar day before;
- morning-of at a configured local clock time;
- 60 minutes before;
- other user-selected relative intervals.

The canonical reminder planner remains provider-neutral and uses the configured canonical **IANA timezone**. Calendar, native notification and spoken notification are projections of the same canonical reminder intent rather than separate reminder records.

## Spoken delivery

`../../tools/reminder_delivery.py` projects canonical reminders into visual notification plus optional spoken-notification intents.

Spoken delivery requires:

- explicit user opt-in;
- a verified native-client notification path;
- a separately verified spoken/TTS capability on the actual device;
- user-selected speech detail level.

Privacy default is generic speech, for example “You have an appointment in one hour.” A user may explicitly allow title-level speech, for example “Cardiology appointment in one hour.”

The voice is generated **on the Android device by its selected Text-to-Speech engine**. M.I.R.R.O.R. supplies the canonical reminder time and speech text; Android synthesizes the audio locally. Android then routes media/TTS audio through the device's currently supported output path, including a connected hearing aid or Bluetooth device when Android has selected that route. The server never pretends it can seize or force a specific Bluetooth route. Visual reminders remain available if spoken delivery is unavailable.

## Reconciliation transaction

For each candidate:
1. read complete relevant evidence;
2. read canonical appointment/source state and dedupe against existing source bindings and Calendar Projection;
3. extract only evidence-backed event fields;
4. resolve provider/person identity from the durable cache before any research;
5. use approved public research only when unresolved;
6. if confidence is below threshold or evidence conflicts, ask rather than write;
7. create/update the canonical appointment and linked provider/entity identity;
8. create/update the linked Calendar event when enabled;
9. generate configured canonical reminders and optional delivery intents;
10. when Calendar projection is enabled, **read the Calendar event back** and verify event ID, target calendar, date/time/timezone, reminders, and source linkage; read every other enabled projection back where the adapter supports it;
11. read canonical state back and verify material fields/source bindings;
12. only after required canonical writes/projections agree mark the evidence reconciled.

Later revision/cancellation evidence updates/cancels the same canonical appointment and projections. Never create a duplicate merely because a new email arrived.

## Scheduler isolation

Appointment reminders are data-driven reminder intents evaluated by the selected control cycle/scheduler and projected to enabled Calendar/native delivery adapters. Do not create one ChatGPT Scheduled Task per appointment.

## Failure contract

- Calendar write/readback failure leaves only that projection unresolved.
- Canonical state write/readback failure blocks reconciliation completion.
- Email ingestion failure does not prevent manual appointment entry.
- Provider-research failure leaves identity/category unresolved or asks the user; it does not invent a specialty.
- Spoken-notification failure degrades to the remaining verified notification path and does not delete the canonical reminder.
- Owner correction updates durable aliases/source bindings and must be read back before claiming the correction persisted.
- Each adapter fails independently.

## Sensitive appointments

Medical or other sensitive appointments may be organized only when selected. Store and speak only the minimum detail allowed by the user's selected policy. Never infer diagnosis, treatment, prognosis, or other medical facts from scheduling evidence or provider specialty.

## Minimal dependencies

Basic appointment tracking needs the selected structured state authority. Email ingestion, Calendar projection, public provider research, visual notification and spoken notification are optional adapters/sub-capabilities.

## Portability

Portable source contains rules/config/schema/migrations/tests only. Real emails, appointments, provider names, medical details, event IDs, reminder history, state rows, device tokens and evidence remain in deployment authorities and are excluded from upstream contributions.
