# Appointments, Calendar, and medication reminders

Email and documents are evidence. Canonical appointment state lives in the structured authority. Calendar is a linked projection/reminder surface.

## Appointment transaction

1. Read complete relevant evidence.
2. Deduplicate by stable source/message/provider identity and canonical Appointment UUID.
3. Ask on conflicting or low-confidence date, time, timezone, person, location, or appointment type.
4. Create or update one linked Calendar event when enabled.
5. Read back event ID, target calendar, title/type, start/end, timezone, reminders, and source link.
6. Write and read back `Appointments` and `Calendar Projection` rows.
7. Revisions and cancellations update the same identities.

Reminder profiles may include day-before, a configured morning-of local clock time, and relative intervals such as one hour before. Put event-specific reminders on the Calendar event; do not create one automation per appointment.

Medication reminders default off. Require an explicit schedule supported by the owner, prescription label, pharmacy, or clinician. Never infer dose/timing, advise on a missed dose, or share with a caregiver without separate consent and exact recipient resolution.
