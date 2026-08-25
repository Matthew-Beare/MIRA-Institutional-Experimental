# Provider onboarding — Google, Microsoft 365, Apple and alternative AI

Life Planner is provider-neutral at the policy and data-contract layer. It is not provider-magical. Every live feature is enabled only after the exact account, resource, permission and readback have been observed.

This is a browser-first guide. A normal user does not open a terminal, install Git or paste credentials into chat. Corporate and regulated users must first complete [`ENTERPRISE_PILOT.md`](ENTERPRISE_PILOT.md).

## Pick one authority for each job

Record these selections in the `Authority Registry`:

| Job | Google lane | Microsoft lane | Apple/manual lane |
|---|---|---|---|
| Structured mutable state | Google Sheets | Microsoft Lists or an explicit Excel table in OneDrive/SharePoint | Numbers exported as CSV/JSON, or another selected database |
| Retained documents/evidence | Google Drive | OneDrive or SharePoint document library | iCloud Drive through deliberate Files/browser upload and download |
| Calendar projection | Google Calendar | Outlook Calendar | ICS import/export to Apple Calendar |
| Mail evidence | Gmail | Outlook | Deliberately uploaded/exported evidence unless a verified adapter exists |
| Durable source | personal/organization Git or managed release | organization Git/Azure Repos/managed release | managed release or optional Git account |

Do not keep the same mutable data class authoritative in two providers. A backup or projection is labelled as such and does not silently become a second truth.

## Common browser-only setup transaction

For every selected provider:

1. Confirm the exact signed-in identity and, for managed accounts, tenant/workspace.
2. Confirm the data classification allowed for the exact AI deployment and provider connection.
3. Select or create one narrowly scoped resource; do not grant an entire drive or tenant by default.
4. Connect the provider through the AI product's approved Apps/Connectors surface or the organization's approved integration.
5. Record the resource name and stable provider ID/URL in the Authority Registry. Never put a secret or mutable record in Git.
6. Prove a bounded read.
7. With explicit provisioning approval, write one harmless synthetic setup record.
8. Read that exact provider record back and compare its ID and contents.
9. Retain or remove the test record under the selected records policy.
10. Record `verified`, `blocked` or `manual`; do not relabel a missing write/readback as installed.

Provider login, connection, app availability, allowed actions, account authorization and runtime permission are separate gates. A visible file or a connected badge proves none of the later gates by itself.

## Google Workspace lane

Use this lane when the selected identity can access Google Drive and the required Google apps.

1. In the approved AI product, open its Apps/Connectors settings and connect only the intended Google account.
2. For structured state, create or select one Google Sheet and record its exact spreadsheet ID. Create the `Authority Registry` and `Interview Ledger` there before enabling stateful modules.
3. For retained evidence, create or select one Google Drive root and record its exact folder ID. Use stable links back to canonical rows.
4. Enable Gmail or Google Calendar only when the selected module needs them. Mail read, Calendar read, Calendar write and Calendar readback are independent capabilities.
5. Run the common bounded read → write → readback transaction for the Sheet, Drive folder and Calendar separately.
6. Keep broad/sensitive OAuth scopes disabled unless the account owner or Workspace administrator explicitly approves them.

The Personal Google beta packages the exact resource schema in `life-planner/assets/personal-google-blueprint.json` and the deterministic plan/readback gate in `life-planner/scripts/google_bootstrap.py`. Use that package instead of inventing tab names or declaring success from a connection badge. It provisions only `core` plus explicitly selected modules, so unused workbooks are not created.

If the runtime can read a Sheet but cannot write and read it back, Life Planner may answer from that Sheet but cannot claim canonical-state mutation.

## Microsoft 365, OneDrive and SharePoint lane

Use this lane for personal Microsoft accounts or an organization-approved Microsoft 365 tenant.

1. Confirm whether the identity is a personal Microsoft account or the exact Entra-managed work/school tenant. Do not cross the two.
2. In the approved AI product, connect the Microsoft/OneDrive/SharePoint app exposed by that product. If the tenant shows an administrator approval request, stop and use that route; do not create a personal account as a workaround.
3. Choose one structured authority:
   - a Microsoft List with explicit columns; or
   - a named Excel table inside one workbook stored in OneDrive/SharePoint.
   A loose range in an arbitrary workbook is not a durable schema.
4. Choose one evidence root: a narrowly scoped OneDrive folder or SharePoint document library. Record the drive/site/library/item identifiers returned by the provider.
5. Enable Outlook mail or Outlook Calendar only for selected modules. Prove mail read, event read, event write and event readback separately.
6. Run the bounded synthetic write/readback transaction against each exact resource.
7. Record Entra consent/admin approval, selected-resource scope and the tested actions. Graph or connector access to one resource does not imply tenant-wide access.

On a locked-down device, all of this can be done in approved browser surfaces. No local OneDrive sync client, PowerShell, Git installation or command prompt is required.

## Apple and iCloud lane

Apple/iCloud support is deliberately honest: it is a user-mediated portability lane unless a specific approved adapter proves more.

1. Use the supported AI product in Safari or another approved browser on iPhone, iPad or Mac.
2. Keep mutable structured data in a selected supported authority, or maintain it in Numbers and deliberately export CSV/JSON for an import transaction.
3. Use iCloud Drive through the Files app or iCloud web interface to select and upload/download documents deliberately.
4. Use ICS export/import for Apple Calendar handoff. Verify the event in Apple Calendar after import.
5. Record every manual import/export with source file, export time, import time and resulting canonical revision so stale files cannot silently overwrite newer state.

Do not claim unattended arbitrary iCloud Drive access, automatic Numbers mutation, background Apple Calendar synchronization or provider readback unless the exact runtime exposes and proves those actions. CloudKit app containers are not general access to every file in a user's iCloud Drive.

## Claude and other AI runtimes

The same Life Planner policy can be used in Claude, an approved Microsoft/VA AI product, Gemini or another MCP-capable runtime, but capabilities are re-evaluated from zero.

1. Pin the exact Life Planner release or connect the approved source repository/managed release.
2. Connect only provider integrations enabled for that exact AI deployment, such as an approved Google Drive integration or remote MCP connector.
3. Run capability discovery for source, structured state, retained evidence, mail, calendar and scheduling.
4. Prove each claimed write with remote provider readback.
5. If scheduling is absent, use an approved external scheduler or manual brief trigger. A copied prompt does not create scheduled-delivery parity.

Never assume that Claude, ChatGPT, Copilot, Gemini or a branded enterprise edition can perform an action merely because another runtime can.

## Institutional and VA deployment

Use the private Institutional-Experimental source channel and synthetic data for evaluation. No PHI/PII, VA-sensitive record or operational state belongs in Git.

Before sensitive runtime use, record the exact organization-approved AI deployment, authenticated identity, ATO or equivalent approval reference, approved purpose/data class, storage tenant/resources, connector actions, retention, audit and incident controls. The product being described as HIPAA-capable, FedRAMP-capable or approved for some VA use is not blanket approval for this workflow.

The sponsor must recheck current organizational guidance at enrollment. Use [`ENTERPRISE_PILOT.md`](ENTERPRISE_PILOT.md) for the acceptance gates and fail closed when any approval evidence is missing.

## Required onboarding readback

The assistant shows this before declaring setup complete:

```text
AI runtime/deployment: observed exact product and workspace/tenant
Signed-in identity class: personal / managed organization
Data classification: public / personal / non-sensitive work / regulated-sensitive
Approval evidence: not applicable / exact current reference / blocked
Durable source: provider + exact repository/release + read/write/readback
Structured state: provider + exact resource + read/write/readback
Evidence store: provider + exact resource + read/write/readback/manual
Mail: disabled / read verified / blocked
Calendar: disabled / read verified / write+readback verified / manual ICS
Scheduling: disabled / observed firing verified / external approved scheduler / manual
Local command line required: no
Unresolved gates: exact next action for each block
```

This readback is evidence, not ceremony. If it cannot name the resource and prove the action, the capability is not installed.
