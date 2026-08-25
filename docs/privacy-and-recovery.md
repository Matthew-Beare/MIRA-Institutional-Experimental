# Privacy and Recovery

## Boundaries

- ChatGPT tasks run in the connected cloud environment. They cannot silently inspect a private phone, home server, NAS, local filesystem, or LAN service.
- A local-device workflow requires an explicitly configured bridge, API, sync folder, or service account with the narrowest practical permission.
- Connectors may lose authorization. Every state-changing automation must perform harmless dependency reads before it is created or rebuilt.
- Never place passwords, API tokens, private keys, full card numbers, or raw mutable operational exports in prompts or this repository.

## Recovery order

1. Inspect the live Sheets and private automation list.
2. Treat those live systems as authority over chat recollection.
3. Validate the checked-in skill and its policy fingerprint.
4. Repair or rebuild only the bounded component the user authorized.
5. Verify the remote repository and scheduled-task state.
6. After one-time private-repository authorization, automatically validate, commit, push, and verify every lasting feature/schema/workflow/schedule/policy/onboarding change; do not ask again whether to push.
7. Never auto-merge, publish publicly, force-push, or commit mutable data/secrets under that standing authorization.
8. Return the complete Project-instructions replacement when the bootstrap contract changed.
