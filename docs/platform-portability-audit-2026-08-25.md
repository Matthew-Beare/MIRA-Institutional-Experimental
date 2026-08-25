# Platform portability and regulated-pilot audit — 2026-08-25

## Outcome

The public starter no longer treats ChatGPT + personal GitHub + Google Workspace as the only valid deployment. It now has a provider-neutral, browser-first capability gate for:

- ChatGPT/Codex, Claude, approved Microsoft/VA AI, Gemini, and generic MCP-capable runtimes;
- personal Git, organization Git, managed central source, and explicit degraded no-Git use;
- Google Sheets/Drive, Microsoft Lists or Excel plus OneDrive/SharePoint, and manual Apple/iCloud or portable-file exchange;
- personal, enterprise-managed, portable-manual, and regulated-sensitive onboarding boundaries.

This is not a claim that every named provider is live or equivalent. The repository proves deterministic routing, fail-closed approval logic, onboarding contracts, and tests. A live provider is enabled only after its exact identity, permissions, bounded write, readback, and—when used—observed schedule firing are proven.

## Root cause found

The previous starter architecture embedded three assumptions in onboarding and configuration:

1. every user would have personal GitHub;
2. ChatGPT/Codex would be the runtime;
3. Google Sheets/Drive would be the mutable state/evidence platform.

Those assumptions worked for the reference deployment but break for Claude users, Microsoft-centric organizations, locked-down devices, centrally managed source, and regulated environments. They also encouraged a dangerous inference: that a connected provider name or readable resource proved write capability. It does not.

## Implemented and tested

- `starter/platform-capabilities.json` records runtime, storage, source, deployment-lane, and claim boundaries.
- `starter/tools/provider_capability_router.py` computes `ready`, `degraded`, or `blocked` only from observed booleans and exact data approval.
- Missing state read/write/readback blocks stateful setup.
- Missing source writes degrade personal mutation without pretending a push occurred.
- Missing email, calendar, evidence, or observed schedule firing is isolated and reported rather than silently accepted.
- Regulated-sensitive data is blocked without exact organization approval and a current evidence reference; a bare approval boolean is insufficient.
- Unknown capability/request keys fail closed.
- Browser onboarding supports user-created GitHub and conditionally permits assistant-created repositories only when an exact approved creation action and resulting metadata readback exist.
- Corporate users can consume a pinned managed release without personal Git or local installation.
- Apple/iCloud is honestly limited to deliberate import/export unless a specific adapter proves more.

## Current external constraints

### OpenAI

Workspace/app enablement, end-user service authorization, source-system permissions, and connector actions are separate gates. ChatGPT Work also cannot assume access to arbitrary local device files or browser tabs. Sources: [OpenAI apps and connector controls](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors), [ChatGPT Work overview](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-overview), and [admin rollout guidance](https://learn.chatgpt.com/docs/enterprise/admin-setup).

### Claude

Claude documents Google Drive and remote MCP integration paths, but a connection does not prove the writes, scheduler, or readback required by this project. Team/Enterprise connector availability and enablement remain organization-controlled. Sources: [Anthropic Google Drive integration](https://support.anthropic.com/en/articles/10166901-using-the-google-docs-integration) and [remote MCP connectors](https://support.anthropic.com/en/articles/11175166-about-custom-integrations-using-remote-mcp).

### Google Workspace

Drive APIs can manage files, but OAuth scope selection, verification, and Workspace administrator controls remain external gates. Sources: [Drive file operations](https://developers.google.com/workspace/drive/api/guides/create-file), [Drive OAuth scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth), and [Workspace app access](https://developers.google.com/identity/protocols/oauth2/production-readiness/google-workspace).

### Microsoft 365

Lists/Excel and OneDrive/SharePoint are candidates, not automatically installed adapters. Microsoft Graph permissions, administrator consent, resource assignment, and tenant policy must be verified. Sources: [selected OneDrive/SharePoint permissions](https://learn.microsoft.com/en-us/graph/permissions-selected-overview) and [Graph permissions overview](https://learn.microsoft.com/en-us/graph/permissions-overview).

### Apple/iCloud

iCloud Drive supports user-mediated browser upload/download. CloudKit is app-container scoped and is not a general API for arbitrary user iCloud Drive contents. Sources: [iCloud Drive browser transfer](https://support.apple.com/guide/icloud/upload-and-download-files-mmad632d1df2/icloud) and [CloudKit containers](https://developer.apple.com/documentation/cloudkit/identifying-an-app-s-containers).

### VA pilot

VA's public guidance dated July 22, 2026 lists approved and gated AI options, but that is not blanket authorization for this project's connectors, storage, purpose, or every data class. GitHub Copilot is listed for coding but not for VA-sensitive data. A facility pilot still needs the exact current VA approval/ATO path and sponsor. Source: [VA Guidance for Generative AI Use](https://department.va.gov/ai/guidance-for-generative-ai-use-at-va/).

## Production acceptance gate

Do not call a provider lane production-ready until all applicable evidence is read back:

1. exact runtime/deployment/authenticated identity;
2. approved data classification and purpose;
3. pinned source plus verified source mutation route or managed change process;
4. canonical state read → bounded write → readback;
5. evidence and calendar read/write/readback when enabled;
6. permission-denial and module-isolation tests;
7. canonical IANA clock, recurrence, notification, duplicate, and observed-firing proof when scheduling is enabled;
8. rollback and audit/provenance evidence.

The current repository supplies the portable contract and gate. Live Microsoft/OneDrive/SharePoint writes, Claude action parity, and a VA-authorized tenant deployment remain external until those proofs exist.
