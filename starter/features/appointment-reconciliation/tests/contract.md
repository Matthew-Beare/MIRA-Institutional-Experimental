# Appointment Reconciliation Acceptance Contract

A compliant deployment must prove:

1. appointment automation is opt-in by event/evidence class;
2. manual appointment tracking works with the canonical structured state authority even when email/Calendar adapters are absent;
3. complete relevant evidence is read before mutation;
4. one canonical appointment/source identity maps to at most one active linked Calendar event;
5. provider type/specialty comes from appointment evidence or approved reliable public research and unresolved conflicts ask rather than guess;
6. provider specialty is never treated as diagnosis/treatment evidence;
7. reminder profiles support multiple rules and fixed local-clock reminders use the event IANA timezone rather than a static UTC offset;
8. create/update is followed by Calendar readback verifying event ID, title/type, time/timezone, reminders, target calendar and source linkage;
9. canonical appointment + Calendar Projection state is written and read back before the source is marked reconciled;
10. revisions/cancellations update the same canonical appointment and linked Calendar event;
11. Calendar handles appointment-specific reminders instead of per-appointment Scheduled Tasks;
12. sensitive appointments use minimum necessary detail and do not create medical inferences;
13. email, Calendar, provider-research and canonical-state failures remain module-scoped and do not fall back to chat/shadow state.