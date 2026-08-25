# Calendar Projection

Load this reference when canonical LifeOS state should create/update Google Calendar events or when first boot configures which event classes are projected.

## Principle

Calendar is a synchronized projection of canonical LifeOS state, not the primary database. Every projected event must have a row in `Calendar Projection` linking the source entity to the Google Calendar event ID so revisions update/cancel the existing event instead of creating duplicates.

## First-boot choices

Offer each event class independently and default to off unless the user chooses it:

- appointments and reservations;
- order delivery dates/windows;
- work trips/departures/arrival commitments;
- subscription/trial renewal or cancellation deadlines;
- bills/payment due dates;
- school/work deadlines;
- maintenance/warranty deadlines;
- selected high-priority tasks;
- user-defined event classes.

Ask which target calendar should receive each enabled class, whether tentative dates should be shown, and whether updated ETAs should move the event automatically. Do not imply that enabling one class enables all others.

## Event identity and updates

Use a stable Projection ID based on source type + source ID + event class. Store source type, source ID, target calendar, Google event ID, title, start/end, source-updated timestamp, projection status and sync timestamp.

- Source revision: update the linked event in place.
- Cancelled source: cancel/delete the linked event according to the user's configured projection policy, while retaining the projection audit row.
- Delivered/completed source: mark/update event according to selected behavior; do not create a second completion event.
- Missing Google event: recreate only after verifying the canonical projection row and avoiding a duplicate by source identity/time/title.

## Delivery projections

If order deliveries are enabled, use carrier/vendor evidence only after shipment correlation. Prefer credible carrier ETA/window; update the same event when ETA changes. A delivery event does not replace the active `Shipments` queue or `Order Events`. Multiple packages may be one order-level event or package-level events according to user preference; default to one order-level event to limit clutter.

## Appointments

Appointments parsed from verified email/Docs/user input may be projected only when date/time/location identity is sufficiently supported. Preserve source provenance and never silently invent confirmation state.

For explicitly enabled appointment reminders, run `scripts/reminder_policy.py` with the canonical IANA timezone. The stock profile plans a day-before local reminder, a configured morning-of local reminder, and a relative reminder (60 minutes by default). Merge equal fire times, suppress any reminder that would occur at/after the appointment, and reconcile the result into the existing linked Calendar event. Provider readback must confirm reminder configuration. This planner does not create per-event ChatGPT automations.

Medication reminders are a separate opt-in service. A schedule is valid only when explicitly confirmed from owner, prescription-label, pharmacy, or clinician evidence. Never infer dose/timing, advise doubling or other missed-dose action, expose more sensitive text than configured, or share with a caregiver unless the user explicitly enables sharing to an exact recipient identity. Project approved reminders through the configured provider and read them back; Calendar/projection failure leaves canonical regimen evidence unchanged and marks only the reminder projection degraded.

## Safety

Creating/updating normal user-selected calendar projections is authorized by the configured projection policy after first-boot approval. Inviting other people, adding external attendees, or sending invitation updates is a separate consequential action and requires explicit authority unless the user deliberately configured that behavior.

Never create a separate automation per event. The consolidated lifecycle/brief pipelines maintain projections.
