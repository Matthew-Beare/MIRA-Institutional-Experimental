# M.I.R.R.O.R. Institutional-Experimental

**M.I.R.R.O.R.** means **Memory, Integration, Reality, Reconciliation, Observation, and Record**. **MIRA** is the **MIRROR Intelligence and Reasoning Assistant**. The deliberately forced acronym is a nod to Dennis E. Taylor's *Bobiverse* books and his fondness for a good forced acronym. M.I.R.R.O.R. is the reality layer that **holds the durable reflection of reality**; MIRA is the intelligence layer when the approved runtime supports it.

This public repository is a sanitised institutional onboarding and pilot source/configuration channel. It contains no live regulated or operational data. Where an organization approves the relevant runtime and data classes, the same portable M.I.R.R.O.R. code can coordinate assets, finances, calendars, email, orders and shipments, receipts and refunds, appointments, tasks, medications and opt-in reminder schedules, documents and knowledge, travel/work context, meals, and custom skills.

> **Magic MIRA on the wall...**

Begin with [`starter/ENTERPRISE_PILOT.md`](starter/ENTERPRISE_PILOT.md), then select an approved provider lane. End users do not need a local shell, Git client, or personal cloud account.

## Hard boundary

This Git repository stores source, schemas, non-secret configuration, and synthetic fixtures only: **no PHI/PII in Git**. Do **not** put PHI, PII, VA-sensitive data, clinical records, employee records, receipts, email bodies, authority IDs, or mutable operational state in Git.

Demonstrations use **generic or synthetic personas**. Sensitive runtime use is blocked until the accountable organization confirms the exact **approved runtime**, **ATO** or equivalent approval scope, identity, purpose, storage, connector actions, retention, and audit controls.

## Create and share new skills

A user or pilot team can describe a recurring workflow to MIRA in ordinary language. MIRA should inspect existing capabilities, define the behavior and data boundaries, implement on a feature branch, add tests and synthetic fixtures, and verify the private or organization-approved deployment.

Reusable work is **private by default** within the pilot deployment or organization. It is not published merely because it exists. When coherent, MIRA asks exactly: **Do you want to make this feature available to other people?** Publication requires sanitization, synthetic fixtures, declared dependencies and permissions, privacy/source tests, a visible public diff, and explicit publication approval before an upstream pull request.

See [`starter/SHARED_FEATURE_WORKFLOW.md`](starter/SHARED_FEATURE_WORKFLOW.md).

This is a generated distribution, not an independent source of truth. It uses the same portable code as Personal-Production and Personal-Experimental. `DEPLOYMENT_CHANNEL.json` pins the canonical source revision.
