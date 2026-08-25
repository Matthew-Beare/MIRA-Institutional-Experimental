# Appointment Reconciliation

## Purpose

Turn user-approved classes of appointment/reservation evidence into one verified canonical appointment in the selected structured state authority and an optional linked Calendar event, then reconcile later revisions/cancellations without duplicates.

Manual appointment tracking works with the canonical state authority alone. Email, Calendar, and provider-research capabilities are optional adapters.

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
- attendee/invitation policy.

## Provider type / specialty enrichment

Prefer explicit appointment evidence. If the message identifies a provider but the provider type is unclear and research is permitted/available:

1. search the provider/clinic name plus location when known;
2. prefer official clinic/provider pages, health-system directories, or another reliable public professional directory;
3. record the evidence URL/source and confidence;
4. normalize a useful organizational label such as `Cardiology`, `Endocrinology`, `Audiology`, `Primary Care`, `Dental`, `Ophthalmology`, etc.;
5. if evidence conflicts or remains unclear, ask instead of guessing.

Provider specialty is an organizational fact, not diagnosis/treatment evidence. Never infer why the user is seeing that specialist.

## Reminder profiles

Support multiple reminder rules globally, per person, and/or per appointment class. Examples:

- one calendar day before;
- morning-of at a configured local clock time;
- 60 minutes before;
- other user-selected relative intervals.

A fixed morning-of reminder is converted into the Calendar provider's supported relative reminder interval using the appointment's IANA timezone and date. Never use a hard-coded UTC offset. If the appointment occurs before the configured morning anchor, follow the configured exception rule or ask.

## Reconciliation transaction

For each candidate:
1. read complete relevant evidence;
2. read canonical appointment/source state and dedupe against any existing Calendar Projection;
3. extract only evidence-backed event fields;
4. resolve appointment type from evidence or approved provider research when possible;
5. if confidence is below threshold or evidence conflicts, ask rather than write;
6. create/update the linked Calendar event when enabled;
7. apply all configured reminders;
8. read the Calendar event back and verify event ID, target calendar, title/type, date/time/timezone, reminders, and source linkage;
9. write/update canonical appointment + Calendar Projection state, including provider/source references and specialty evidence where appropriate;
10. read canonical state back;
11. only after required projections and canonical state agree mark the evidence reconciled.

Later revision/cancellation evidence updates/cancels the same canonical appointment and linked Calendar event. Never create a duplicate merely because a new email arrived.

## Reminders and scheduler isolation

Calendar owns appointment-specific reminders when enabled. ChatGPT may surface upcoming appointments through consolidated briefs/accountability dispatchers. Do not create one Scheduled Task per appointment.

## Failure contract

- Calendar write/readback failure leaves the projection unresolved and does not mark canonical reconciliation complete.
- Canonical state write/readback failure leaves the source unresolved even if Calendar changed; read both surfaces before any corrected retry.
- Email ingestion failure does not prevent manual appointment entry.
- Calendar failure does not corrupt canonical appointment state.
- Provider-research failure leaves specialty unresolved or asks the user; it does not block a clearly dated appointment unless type is required by policy.
- Each adapter fails independently.

## Sensitive appointments

Medical or other sensitive appointments may be organized only when selected. Store the minimum detail needed for the chosen reminder/organization workflow. Never infer diagnosis, treatment, prognosis, or other medical facts from scheduling evidence or provider specialty.

## Minimal dependencies

Basic appointment tracking needs the selected structured state authority. Email ingestion, Calendar projection, and public provider research are optional adapters.

## Portability

Portable source contains rules/config/schema/migrations/tests only. Real emails, appointments, provider names, medical details, event IDs, reminder history, state rows, and evidence remain in the deployment authorities and are excluded from upstream contributions.