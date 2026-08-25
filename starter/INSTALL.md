# Install MIRROR — Browser only, No Command Prompt

This is the default browser-only setup path for a person who does **not** know Git and does not want to become a developer just to organize their life.

Do **not** open Command Prompt, PowerShell, Terminal, Git Bash, or a code editor. Do **not** install Git or GitHub CLI. Do not copy commands, tokens, SSH keys, passwords, recovery codes, or other credentials into ChatGPT.

If you already know Git, lovely. Ignore the urge to turn onboarding into a certification exam. The default path is still the browser.

## First: what are MIRROR and MIRA?

- **MIRROR** is the system that keeps the durable record of what is actually true: state, integrations, evidence, reconciliation, and provenance.
- **MIRA** is the default assistant that talks with you, reasons, plans, recommends actions, uses approved tools, and verifies the result back against MIRROR.

The short branding phrase is **“MIRA, mirror on the wall.”**

## Git explained for somebody who has never used it

You only need five ideas:

1. **Git** is an undo history for files. It remembers versions so a bad change can be found and reversed.
2. **GitHub** is a website that stores a Git project online.
3. A **repository** (people say “repo”) is the project folder on GitHub.
4. A **commit** is a named save point: “these files looked like this at this moment.”
5. A **push** means putting a new commit onto GitHub.

You do **not** need to type Git commands during normal MIRROR onboarding.

Why MIRROR uses Git at all: rules, schemas, configuration, tests, and feature code should have a trustworthy change history. Your constantly changing life records do not belong in Git just because Git exists. Tasks, appointments, receipts, routines, meal history, and similar mutable state live in the selected canonical state/evidence authorities.

A useful mental picture:

```text
MIRA talks and reasons
        ↓
MIRROR reconciles reality
        ↓
GitHub keeps version history for the rules/code
State authorities keep the current life data
```

## What you need for the normal personal setup

- a web browser;
- a ChatGPT account where the GitHub app and Codex are available;
- a free GitHub account with a verified email address; and
- roughly ten minutes of clicking through setup screens.

You do not need a local developer environment.

## Choose the deployment lane

### A. Personal browser lane

This is the normal home-user path. You create a private GitHub repository from the public starter, let ChatGPT read it, and let Codex or another verified source-writing tool make durable code/config changes.

### B. Corporate, government, health-care, or locked-down lane

Open [`ENTERPRISE_PILOT.md`](ENTERPRISE_PILOT.md) first.

Do not create a personal GitHub, Google, Microsoft, Apple, or AI account to bypass workplace policy. An organization may use approved GitHub Enterprise, GitLab, Azure Repos, or a managed central source instead. Use synthetic or public data until the exact AI deployment, identity, data classification, storage, and connector actions are approved.

### C. Portable manual lane

If connectors are blocked, MIRROR can still use a pinned release plus deliberate CSV/JSON/ICS/document import and export. That is manual portability, not unattended synchronization. Do not pretend a blocked connector is secretly working because the file format looks hopeful.

## Step 1 — Create or sign in to GitHub

If you already have a personal GitHub account, sign in and go to Step 2.

If not:

1. Open GitHub sign-up: https://github.com/signup
2. Follow the prompts.
3. Verify your email address.
4. Set up two-factor authentication when GitHub offers it.

Never give MIRA, ChatGPT, Codex, or another assistant your GitHub password, verification code, recovery code, access token, or SSH key.

## Step 2 — Make your private MIRROR repository

This creates **your copy** of the project. Think “copy this starter folder into my own private GitHub account,” not “learn software development.”

1. Open the starter template: https://github.com/Matthew-Beare/Daily-Ops-Brief/generate
2. If GitHub shows the public repository instead, select **Use this template** and then **Create a new repository**.
3. For **Owner**, choose your own GitHub account.
4. For the repository name, use something simple such as `mirror-personal`.
5. Select **Private**.
6. Leave **Include all branches** off.
7. Select **Create repository from template**.

Do not substitute a fork, Codespace, ZIP download, local clone, or command-line copy during normal onboarding.

If **Use this template** is missing, stop and report:

```text
Starter blocked — upstream is not enabled as a GitHub template.
```

Do not substitute a fork.

When GitHub finishes, the top of the page will show a name like:

```text
your-github-name/mirror-personal
```

That `owner/repository` name is safe to give the onboarding assistant. Do not give it passwords or tokens.

## Step 3 — Give ChatGPT read access

The ordinary ChatGPT GitHub app is read-only. This lets ChatGPT inspect the repository, but it does **not** prove anything can write changes back.

1. In ChatGPT, open **Settings → Apps**.
2. Find **GitHub** and choose **Connect**.
3. On GitHub, authorize only your new MIRROR repository unless you deliberately want broader access.
4. Return to ChatGPT.

If GitHub was already connected, use the GitHub app configuration to add the new repository.

The assistant must verify the exact repository, owner, visibility, default branch, and current commit. Merely seeing “GitHub connected” is not enough.

## Step 4 — Give Codex write access

ChatGPT's ordinary GitHub connection may be read-only. MIRROR needs a separate verified source-writing capability if you want lasting rules/configuration/features updated automatically.

1. Open **Codex** from ChatGPT.
2. Select **Connect to GitHub** if shown.
3. Authorize the exact MIRROR repository.
4. Create or select the repository environment if Codex asks for one.
5. Return to the onboarding conversation.

If Codex or another verified write path is unavailable, report:

```text
Source setup blocked — ChatGPT can read the repository, but no verified GitHub write capability is available.
```

Do not claim installation succeeded. Do not send the user to Command Prompt as a fallback.

The user can still answer onboarding questions while source writes are blocked, but durable code/config changes remain blocked until a write-capable source lane is verified.

## Step 5 — Verify the boring but important bits

Before MIRA starts asking about your life, it must read back what was actually observed.

For the personal ChatGPT/Codex lane, show something like:

```text
Repository: owner/name
Visibility: private
Default branch: main (or observed default)
Starter commit: observed commit ID
ChatGPT read: verified / blocked
Codex write: verified / blocked
Local command line required: no
Deployment lane: personal browser
AI runtime: observed ChatGPT/Codex deployment
Product: MIRROR
Default assistant: MIRA
Data classification: personal/public/non-sensitive
Source mode: user Git
Structured state provider: observed / blocked
Evidence provider: observed / manual / blocked
Organization approval: not applicable
Organization approval reference: not applicable
```

`Verified` means the capability was actually observed. A button, authorization page, local file, product logo, or read-only result is not proof of write access.

## Step 6 — Start first boot

After the capability readback:

1. Read [`../docs/BRANDING.md`](../docs/BRANDING.md).
2. Apply **MIRROR** as the product/platform identity and **MIRA** as the default assistant identity.
3. Open [`START_HERE.md`](START_HERE.md).
4. Begin the bounded first-boot interview.

The owner may later choose a private nickname. That does not rename the upstream MIRROR project or erase the MIRA/MIRROR architectural terms.

Before creating new connections, MIRA should inspect existing accessible capabilities and evidence. It should not make somebody retype their life because software enjoys forms.

## What happens after first boot

MIRROR will select or create the smallest useful set of authorities, such as:

- a structured state store for tasks/plans/appointments/routines;
- an evidence/document store when retained files matter;
- Calendar when event projection/reminders are useful;
- Git or an approved managed source for rules/config/schema/features/tests.

The first coherent source write requires the user's bounded provisioning approval. After that, when standing source-write authority exists, lasting behavior/config/schema/feature changes should validate, commit, push, and receive remote readback without repeatedly asking whether the user wants version history to function like version history.

Routine mutable state updates still go to the canonical state authority, not Git.

## Other AI runtimes and enterprise environments

MIRROR can be portable across ChatGPT, Claude, Microsoft/VA AI, Gemini, and other capable runtimes, but the name of a product does not prove its connector permissions or feature parity.

Read [`PLATFORM_PORTABILITY.md`](PLATFORM_PORTABILITY.md). The runtime must verify exact read, bounded write, readback, scheduling, and data-approval capabilities.

For corporate or regulated environments, the capability router `provider_capability_router.py` evaluates evidence for the assistant. The end user does not run it manually.

If approval is missing, report:

```text
Enterprise setup blocked — use synthetic/non-sensitive data until the exact AI runtime, storage, purpose, and connector actions are organization-approved.
```

## Things the non-technical installer must never do

- Do not ask the user to install Git.
- Do not ask the user to open a terminal.
- Do not ask the user for a password/token/SSH key.
- Do not treat ChatGPT read access as Codex write access.
- Do not silently make a public repository.
- Do not create personal accounts to bypass workplace controls.
- Do not claim Claude, Microsoft/VA AI, Gemini, ChatGPT, or another runtime has a capability until the exact capability is observed.
- Do not put ordinary mutable personal state into GitHub for convenience.
- Do not claim a push succeeded until the remote commit is read back.

## Developer-only alternative

Developers may use local Git and command-line workflows when they explicitly choose developer mode. That is not the default onboarding path and is never used as the fallback for a confused non-technical user.
