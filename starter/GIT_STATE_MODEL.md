# Git Source / State Boundary

This filename is retained for compatibility with deployments created from the short-lived Git-native-state starter. **Git is not the default mutable personal-state database.**

Read [`STATE_AUTHORITY_MODEL.md`](STATE_AUTHORITY_MODEL.md) for the current architecture.

## Current contract

- Git is the durable source/version authority for code, policy, schemas, migrations, non-secret configuration, feature manifests, tests, onboarding, upstream provenance, and custom-feature lineage. It may be personal GitHub, approved organization GitHub/GitLab/Azure Repos, or managed central source; the end user does not always need a Git account.
- Google Sheets is the default structured mutable-state authority for new-user deployments.
- Google Drive is the default retained evidence/document authority when selected.
- Google Calendar is an optional projection/reminder surface.
- Microsoft Lists/Excel, OneDrive/SharePoint, and Outlook Calendar are supported authority candidates when an approved adapter proves the same read/write/readback contract.
- Apple/iCloud is manual import/export unless a specific approved adapter proves otherwise; do not claim general iCloud Drive automation.
- Other supported databases may replace Sheets only when explicitly selected and able to satisfy the same read/write/dedupe/readback contract.
- Chat history is an intake surface, never the sole database.

Do not store routine mutable personal records such as recipes, appointments, tasks, routines, meal history, shopping rows, receipts, or medical-event scheduling as Git state files merely for versioning convenience.

After standing Git authorization, lasting **behavior/config/schema** changes validate, commit, push, and receive remote readback. Mutable operational changes write to their canonical state authority and are verified there.

When a custom feature is ready to share, ask exactly `Do you want to make this feature available to other people?` and export only sanitized portable behavior/schema/tests, never another person's live Sheets/Drive/Calendar data.
