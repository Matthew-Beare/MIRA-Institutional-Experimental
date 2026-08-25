# Personal Google onboarding

Use this browser-only lane for personal, non-regulated data. Never send a non-technical user to a terminal.

## Required capabilities

- one private user-controlled repository made from the public Life Planner template;
- verified repository read, write, remote readback, and green CI;
- one exact Google identity for Drive and the structured-state workbooks;
- Gmail only when selected email evidence requires it;
- Google Calendar only when selected projections/reminders require it;
- a notification-capable scheduler only when recurring delivery is selected.

Connection badges are not evidence. Read back the authenticated profile for GitHub, Drive, Gmail, and Calendar separately.

## Bootstrap transaction

1. Verify the public template repository and exact upstream commit.
2. Verify the user's private repository owner, visibility, default branch, head commit, read access, and write access.
3. Collect the four kickoff answers, canonical IANA timezone, enabled modules, and Google identity.
4. Ask whether the user wants recurring briefs. If yes, ask for each exact local time and notification mode. Do not offer, infer, or inherit a stock time. Validate the chosen schedule with `scripts/brief_schedule.py` and keep the non-secret schedule in that user's version-controlled deployment configuration.
5. Create a deployment UUID and owner UUID. Keep the resulting provider plan out of portable Git because it contains personal provider references.
6. Run `google_bootstrap.py plan` with the bundled blueprint and question bank.
7. Create the planned native Google workbooks and tabs. Preserve header order exactly, set each native spreadsheet's timezone property to the canonical IANA timezone, and read that property back.
8. Create the planned Drive root/folders and move or link evidence resources there when the provider permits it.
9. Populate `Metadata`, `Authority Registry`, `Interview Ledger`, `Integration Registry`, `People`, and `Services` from the plan. Record the selected brief service, timezone and slots in `Services`; Git remains authoritative for the durable schedule configuration.
10. If Gmail is enabled, prove a bounded read without changing mail.
11. If Calendar is enabled, create one clearly synthetic setup event, read it back, record its provider ID, then remove or retain it according to the user's test-record policy.
12. Build an observed readback document from provider responses and run `google_bootstrap.py verify --strict`. Use unformatted cell values for readback; the verifier compares offset-aware ISO and Excel/Sheets serial timestamps as instants while keeping all other seed fields strict.
13. Generate the deployment's non-secret policy/config/schema files, including its selected brief schedule when enabled. Validate, commit, push, read back the remote commit, and require green CI.
14. If recurring delivery is enabled, project that exact committed schedule into the selected scheduler using the fewest provider objects needed, read back timezone and slots exactly, and do not call scheduling healthy until one real firing and Run Log record are observed.

## Schedule changes after onboarding

A later request such as moving a brief, adding one, disabling one, changing notification mode, or changing canonical timezone is a durable behavior/configuration change. Read the user's current schedule from source, apply only the requested change, validate it, commit/push/read back the new source revision, reconcile the scheduler, and then read back the scheduler definition. Never change only the provider scheduler and leave source describing the old schedule.

## Ready means

The bootstrap verifier returns `ready`, source CI is green, and every selected live provider action has exact readback. A deployment awaiting its first scheduled firing is `degraded`, not failed and not fully proven.
