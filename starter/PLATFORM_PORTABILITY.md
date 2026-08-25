# Platform portability contract

Personal Ops Planner has a portable policy/data core and platform adapters. It does **not** pretend that ChatGPT, Claude, Microsoft Copilot, Gemini, Google Drive, OneDrive, SharePoint, or Apple/iCloud expose the same tools.

The machine-readable catalog is [`platform-capabilities.json`](platform-capabilities.json). The onboarding assistant evaluates observed capabilities with `tools/provider_capability_router.py`; the human never runs that script or opens a terminal.

## Portable core

The following artifacts are vendor-neutral:

- Markdown policy and onboarding contracts;
- JSON schemas, feature manifests, and capability requirements;
- stable UUID identity and provenance rules;
- provider-neutral Authority and Integration Registries;
- CSV/JSON data interchange and ICS calendar interchange;
- read → correlate/dedupe → bounded write → provider readback mutation semantics;
- module-scoped failure and circuit-breaker behavior.

An AI runtime may use the core only to the extent that its **observed** tools and permissions satisfy those contracts. A provider name, connection button, readable file, or marketing claim is not proof of write access, scheduling, or readback.

## AI runtime lanes

| Runtime | Useful documented paths | What remains capability-gated |
|---|---|---|
| ChatGPT / Codex | plugins/connected apps; GitHub read through the ChatGPT app; separate Codex source writes | exact app actions, workspace permissions, state/evidence writes, scheduling, notifications, source remote readback |
| Claude | GitHub and Google Drive integrations; remote MCP connectors | connector write actions, organization enablement, scheduled delivery, state-store read/write/readback |
| Microsoft Copilot or another organization-approved AI | Microsoft 365 and organization-managed capabilities when the tenant exposes them | exact product, identity, data classification approval, Graph/connector scopes, actions, readback, scheduling |
| Gemini | Google-account or Workspace capabilities when exposed | exact plan/admin policy, actions, readback, scheduling |
| Other MCP-capable AI | portable contracts through an approved remote MCP or equivalent adapter | every live capability until tested; no feature parity is inferred |

Prompts and policy can be exported to another AI. Platform-only mechanics cannot. For example, a ChatGPT Scheduled Task does not become a Claude or Copilot schedule merely because the same Markdown instructions are copied.

## Storage lanes

### Google Workspace

- structured state candidate: Google Sheets;
- retained evidence: Google Drive;
- optional calendar/email adapters: Google Calendar and Gmail;
- broad or sensitive OAuth scopes and Workspace app access may require verification or administrator approval.

### Microsoft 365

- structured state candidates: Microsoft Lists or an explicit Excel table stored in OneDrive/SharePoint;
- retained evidence: OneDrive or a SharePoint document library;
- optional calendar/email adapters: Outlook through an approved connector or Microsoft Graph;
- Entra consent and resource permission are separate. Prefer delegated, least-privilege, resource-selected access when the organization supports it.

### Apple/iCloud

Apple/iCloud is a supported **user experience**, not a falsely advertised automatic database adapter:

- iPhone, iPad, and Mac users can use any supported web AI runtime and upload/download portable files;
- iCloud Drive may be used through user-mediated browser or Files-app import/export;
- ICS and CSV/JSON provide portable handoff formats;
- do not claim general automated access to a user's iCloud Drive. Apple's CloudKit APIs operate on app-owned containers rather than exposing arbitrary iCloud Drive contents as a universal backend.

### Portable files

When every connector is blocked, a user can still use versioned releases plus deliberate CSV/JSON/ICS and document import/export. That lane is manual. Unattended synchronization, write automation, and provider readback remain disabled.

## Source/version lanes

1. **Personal GitHub:** the existing browser template workflow; private personal repository by default.
2. **Organization Git:** approved GitHub Enterprise, GitLab, or Azure Repos with exact read/write/readback verification.
3. **Managed central source:** administrators maintain and audit the release; end users consume a pinned version. A user does not need a Git account, but personal behavior changes enter the approved change process.
4. **No Git available:** portable/manual use may continue, but lasting personal source changes are not called durable and cannot be auto-committed.

The phrase **managed central source** does not mean mutable user state is stored in Git. State remains in its selected canonical authority.

## Capability readback

Before enabling a module, persist:

- runtime and exact deployment/tenant;
- data classification and a current approval-evidence reference for regulated-sensitive use;
- source mode and observed source read/write/readback;
- structured-state provider/resource and observed read/write/readback;
- evidence provider/resource and observed read/write/readback;
- optional email/calendar/scheduler capabilities;
- module health and one next action for each block.

Re-run discovery after an admin changes policy, a connector is replaced, or a provider changes behavior.

## Current primary references

- [OpenAI plugin and connector controls](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors)
- [OpenAI ChatGPT Work execution and connected-app boundaries](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-overview)
- [Anthropic Google Drive integration](https://support.anthropic.com/en/articles/10166901-using-the-google-docs-integration)
- [Anthropic remote MCP connectors](https://support.anthropic.com/en/articles/11175166-about-custom-integrations-using-remote-mcp)
- [Google Drive OAuth scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)
- [Google Workspace app-access considerations](https://developers.google.com/identity/protocols/oauth2/production-readiness/google-workspace)
- [Microsoft Graph selected OneDrive/SharePoint permissions](https://learn.microsoft.com/en-us/graph/permissions-selected-overview)
- [Apple iCloud Drive browser upload/download](https://support.apple.com/guide/icloud/upload-and-download-files-mmad632d1df2/icloud)
- [Apple CloudKit app containers](https://developer.apple.com/documentation/cloudkit/identifying-an-app-s-containers)

These links explain potential integration surfaces. They never replace live tenant/provider verification.
