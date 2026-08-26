# Appointment Reconciliation Acceptance Contract

A compliant deployment must prove:

1. appointment automation is opt-in by event/evidence class;
2. manual appointment tracking works with the canonical structured state authority even when email/Calendar adapters are absent;
3. complete relevant evidence is read before mutation;
4. one canonical appointment/source identity maps to at most one active linked Calendar event;
5. provider/person identity checks durable source bindings, aliases and contacts before public research;
6. supported public research is retained with provenance/confidence and reused rather than repeated for every appointment;
7. owner correction updates the durable provider/entity binding so the same known sender/name is not repeatedly misidentified;
8. provider type/specialty comes from appointment evidence, durable verified identity, owner correction, or approved reliable public research; unresolved conflicts ask rather than guess;
9. provider specialty is never treated as diagnosis/treatment evidence;
10. reminder profiles support multiple rules and fixed local-clock reminders use the event IANA timezone rather than a static UTC offset;
11. one canonical reminder may project to Calendar, visual native notification and/or spoken native notification without becoming duplicate reminder state;
12. spoken reminders are opt-in, default to generic privacy-preserving speech, require verified native-client spoken delivery, and degrade without deleting the visual/canonical reminder;
13. native clients own TTS/audio routing; server code does not claim direct control over a Bluetooth hearing aid or speaker route;
14. create/update is followed by applicable projection readback verifying IDs/material fields when the adapter supports readback;
15. canonical appointment/provider + Calendar Projection state is written and read back before the source is marked reconciled;
16. revisions/cancellations update the same canonical appointment and linked projections;
17. the selected scheduler/control cycle handles appointment reminder intents instead of creating one ChatGPT Scheduled Task per appointment;
18. sensitive appointments use minimum necessary stored/spoken detail and do not create medical inferences;
19. email, Calendar, provider-research, notification and canonical-state failures remain module-scoped and do not fall back to chat/shadow state.
