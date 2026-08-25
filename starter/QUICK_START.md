# Start MIRA | M.I.R.R.O.R.

**M.I.R.R.O.R.** means **Memory, Integration, Reality, Reconciliation, Observation, and Record**. **MIRA** is the **MIRROR Intelligence and Reasoning Assistant**. The deliberately forced acronym is a nod to Dennis E. Taylor's *Bobiverse* books and their fondness for a good forced acronym. M.I.R.R.O.R. is the private reality layer that **holds the durable reflection of reality**; MIRA is the assistant that talks with you and reasons over that reflection.

You do not need to know programming. You do not need a command prompt. You do not need to type Git commands.

## What it can keep track of

With the connections you choose, M.I.R.R.O.R. can organize and connect things such as assets and inventory, finances and reimbursements, calendars, email, orders and deliveries, receipts and refunds, appointments, tasks and projects, medications and opt-in reminder schedules, documents and knowledge, travel and work, mileage, meals and groceries, and new areas you ask MIRA to add.

Your changing personal facts belong in the private state provider selected during setup. They do not belong in the public source template.

> **Magic MIRA on the wall...**

## What Git and GitHub mean

**Git is version history.** It keeps a record of changes to the rules and code so a bad change can be traced or rolled back.

**GitHub is the website that stores those versioned files.** Think of it as the filing cabinet for M.I.R.R.O.R.'s instructions, not the place where all of your private life data must live.

Passwords, tokens, medical records, private email bodies, receipts, and other sensitive operational data do not belong in public source.

## Personal browser setup

### 1. Sign in to GitHub

Use a normal web browser. If you do not have a personal GitHub account, create one at GitHub and verify the email address.

Never give MIRA your GitHub password, verification code, recovery code, token, or SSH key.

### 2. Make your private source copy

Open the current public M.I.R.R.O.R. Personal-Experimental onboarding repository in GitHub and use its documented browser-copy/template path to create your own private repository.

On the GitHub page:

1. Choose **your own GitHub account** as Owner.
2. Give the repository a neutral name such as `my-mirror`.
3. Choose **Private**.
4. Leave any option that copies experimental branches off unless the release instructions explicitly require it.
5. Create the repository using the browser workflow documented for that release.

If the expected browser-copy control is missing, stop and use [`INSTALL.md`](INSTALL.md). Do not improvise with a Codespace, local command line, or a public personal repository.

### 3. Give ChatGPT read access

In ChatGPT, open **Settings → Apps → GitHub** and connect the exact private repository you just created.

This proves read access only.

### 4. Give Codex write access

Open Codex in ChatGPT and authorize that same private repository.

The ordinary ChatGPT GitHub app is read-only. Codex write access is a separate capability and must be proven by an actual bounded write plus remote readback before setup is called complete.

### 5. Give MIRA the repository name

Send only the non-secret repository name in this form:

`your-name/your-repository`

MIRA must verify:

- owner;
- private visibility;
- default branch;
- current commit;
- ChatGPT read access; and
- Codex write/readback capability.

No Command Prompt is required.

### 6. Let MIRA finish setup

The installed package may still use the internal compatibility ID `life-planner`. That is an implementation ID, not the public product name.

MIRA installs and validates the portable package, verifies the selected state/evidence provider, then starts first boot.

The defaults are already settled:

- System: **M.I.R.R.O.R.**
- Assistant: **MIRA**
- Ask the user to invent a system name: **No**

If a legacy onboarding document asks what the system should be called, MIRA resolves that item to **M.I.R.R.O.R.** automatically unless you explicitly choose a private alias.

## Make M.I.R.R.O.R. do something new

You do not need to write code yourself. Tell MIRA what recurring problem you want solved in normal language.

For example:

`Design a skill that tracks maintenance for my tools and reminds me when service is due.`

MIRA is expected to inspect what already exists, design the new behavior, put the work on a feature branch, define any required data/permissions/connections, add tests and synthetic examples, test it, and commit a verified checkpoint.

The new skill stays private unless you approve sharing it. When it is ready, MIRA asks: **Do you want to make this feature available to other people?**

If you say yes, MIRA must remove your personal data and identifiers, use synthetic examples, run privacy and source checks, show you exactly what would become public, and only then create a sanitized upstream contribution under explicit approval. See [`SHARED_FEATURE_WORKFLOW.md`](SHARED_FEATURE_WORKFLOW.md).

## Corporate, government, health-care, or locked-down devices

Do not create personal GitHub, cloud, or AI accounts to bypass workplace policy. Start with [`ENTERPRISE_PILOT.md`](ENTERPRISE_PILOT.md). Approved organization Git or a managed central source may replace personal GitHub.

## If something goes wrong

Use [`INSTALL.md`](INSTALL.md) for the detailed browser-only troubleshooting path and capability readback fields. Do **not** open Command Prompt, PowerShell, Terminal, Git Bash, or install Git/GitHub CLI as a fallback for normal onboarding.

If anything asks you to paste a password, one-time code, recovery code, token, or SSH key into chat, stop.
