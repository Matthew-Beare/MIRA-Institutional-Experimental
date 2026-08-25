# MIRA | M.I.R.R.O.R.

## Brand contract

**M.I.R.R.O.R.** stands for **Memory, Integration, Reality, Reconciliation, Observation, and Record**:

- **M**emory
- **I**ntegration
- **R**eality
- **R**econciliation
- **O**bservation
- **R**ecord

**MIRA** is the **MIRROR Intelligence and Reasoning Assistant**.

The deliberately forced acronym is a nod to Dennis E. Taylor's *Bobiverse* books and their fondness for a good forced acronym.

**M.I.R.R.O.R. is the reality layer. MIRA is the intelligence layer.**

M.I.R.R.O.R. **holds the durable reflection of reality**: the evidence-backed state, relationships, history, reconciliation, observations, and provenance that describe the user's world. MIRA is the assistant that converses with the user, reasons over that reflection, plans, recommends, and carries out approved actions.

> **Magic MIRA on the wall...**

### Public styling and machine identifiers

Use **M.I.R.R.O.R.** in human-facing prose when practical. Use `MIRROR` in code, configuration, paths, and other punctuation-sensitive identifiers. The default assistant name is **MIRA**; normal prose may use **Mira**.

### What M.I.R.R.O.R. can reflect

With user-approved integrations and authorities, M.I.R.R.O.R. can maintain connected state and evidence for domains such as:

- assets, inventory, identifiers, manuals, warranties, maintenance, and specifications;
- finances, reimbursements, charges, refunds, and supporting evidence;
- calendars, appointments, reservations, and reminders;
- email and actionable correspondence;
- orders, shipments, receipts, cancellations, replacements, and refunds;
- tasks, projects, routines, work, travel, and mileage;
- medications and opt-in reminder schedules based only on explicit verified regimen information;
- documents, knowledge, meals, groceries, and other user-defined domains.

The system is intentionally extensible. New portable skills follow the shared-feature lifecycle and privacy gate rather than creating one-off undocumented behavior.

### M.I.R.R.O.R. layer

M.I.R.R.O.R. owns the evidence-backed model of reality:

- memory;
- integrations;
- evidence and observations;
- Reality Record;
- reconciliation; and
- provenance.

### MIRA layer

MIRA owns the intelligence surface:

- conversation;
- reasoning;
- planning;
- recommendations; and
- approved execution.

MIRA must reason from M.I.R.R.O.R.'s verified reality. Inference may be proposed, but it must not silently become canonical state.

## Release-channel branding

The human-facing channel names are:

- **M.I.R.R.O.R. Personal-Production**;
- **M.I.R.R.O.R. Personal-Experimental**; and
- **M.I.R.R.O.R. Institutional-Experimental**.

The current repository names are:

- `MIRA-Personal-Production`;
- `MIRA-Public-Experimental`; and
- `MIRA-Institutional-Experimental`.

All three repositories are public onboarding surfaces. Public visibility never authorizes live personal, regulated, or operational data in Git. Every channel uses the same portable application code from the same canonical source revision. Differences are limited to deployment policy, approved runtime/provider configuration, data classification, and mutable external state. Do not maintain channel-specific feature forks.

## New-user naming

A new deployment does **not** ask the user to invent the system or assistant name. The defaults are **M.I.R.R.O.R.** and **MIRA**. A user may later choose a private assistant alias, but that mutable preference does not rename upstream source or the product.

## Skill creation and sharing

A user may ask MIRA in normal language to design a new skill. MIRA should inspect existing capabilities first, define the skill's behavior and authorities, implement it on a feature branch, add tests and synthetic fixtures, verify it in the private deployment, and commit a coherent checkpoint.

A working personal skill is **private by default**. When it becomes reusable, MIRA asks exactly: **Do you want to make this feature available to other people?** Publication requires explicit approval plus sanitization, synthetic fixtures, declared dependencies/permissions, privacy and source audits, a visible public diff, and an upstream pull request. Standing permission to version the user's private repository is never permission to publish.

See [`../starter/SHARED_FEATURE_WORKFLOW.md`](../starter/SHARED_FEATURE_WORKFLOW.md).

## Legacy compatibility identifiers

**Life Planner** is a former working name. During bounded migration, `life-planner`, legacy automation titles, historical evidence labels, and other implementation identifiers may remain where changing them would break dependencies.

Do not perform a cosmetic bulk rename of live automations, provider resources, schema keys, historical evidence, or installed package IDs. Migrate live identifiers only with dependency inspection, rollback, provider/source readback, and observed execution where relevant.

Before commercial launch, perform proper trademark/domain/app-store clearance for the final public brand. A repository rename or web search is not legal clearance.
