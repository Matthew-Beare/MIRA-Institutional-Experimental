# Architecture

The system separates mutable state, deterministic policy, evidence, scheduled dispatch, and versioned recovery material.

| Layer | Authority | Responsibility |
|---|---|---|
| Mutable Ops state | Ops Status Register | Tasks, controls, routes, trips, shipments, suppressions, run logs |
| Mileage state | Mileage & Pay Tracker | Company-paid miles, frozen rate, gross estimate, pay-week history |
| Purchase state | Purchase & Receipt Archive | Transactions, items, lifecycle events, expense allocations, classification queue, audit gate |
| Evidence | Gmail, Calendar, Drive | Complete threads, appointments, receipt attachments and archives |
| Policy | `skill/ops-brief-policy` | Routing, invariants, deterministic workflow, failure boundaries |
| Control-cycle dispatcher | One ChatGPT task | Reconcile receipts/orders, run the PM qualified-job watch, and emit briefs at 2:45 AM and 2:45 PM Eastern |
| Recovery | Private GitHub repository | Tests, templates, documentation, policy fingerprints |

The task carries no mutable database. The dispatcher chooses the slot and invokes the skill; receipt/order, qualified-job, and brief phases remain separate failure domains inside one scheduled run. Receipt work must pass the Audit gate before archiving source mail. No order, job, or calendar event receives its own automation.

See [LyfeOS 0.0.1 Data Model](lyfeos-data-model.md) for keys, relationships, and the self-hosting boundary.

The generic starter is separate from the current deployment. It may generate a new bootstrap contract, but it must not inherit the current user's identifiers or operational rows.

## Portable deployment architecture

The reference deployment above uses Google authorities and ChatGPT scheduling. The reusable starter does not hard-code those providers:

| Portable role | Personal candidate | Microsoft/enterprise candidate | Apple/manual candidate |
|---|---|---|---|
| AI runtime | ChatGPT/Codex or Claude | approved Microsoft/VA AI, ChatGPT FedRAMP, Claude for Gov, or another tenant-approved runtime | any approved web runtime |
| Source lineage | private GitHub template | GitHub Enterprise, GitLab, Azure Repos, or managed central source | pinned managed release |
| Structured state | Google Sheets | Microsoft Lists or explicit Excel tables in OneDrive/SharePoint | CSV/JSON manual exchange |
| Evidence | Google Drive | OneDrive or SharePoint document library | iCloud Drive/user-mediated file exchange |
| Calendar projection | Google Calendar | Outlook Calendar | ICS manual exchange |

These are candidates, not installation claims. `starter/platform-capabilities.json` and `starter/tools/provider_capability_router.py` require observed capability-level read/write/readback. A provider name never proves access, feature parity, scheduling, or organization approval.

Regulated deployments use `starter/ENTERPRISE_PILOT.md`. Personal accounts and public services are never used to bypass organization policy.
