# Install Personal Ops Planner — Browser only, No Command Prompt

This is the default browser-only setup path for a non-technical user. Do **not** open Command Prompt, PowerShell, Terminal, Git Bash, or a code editor. Do **not** install Git or GitHub CLI. Do **not** copy commands, tokens, SSH keys, or passwords.

The personal ChatGPT/Codex lane has three separate jobs:

1. GitHub creates a private personal copy of the public starter.
2. The ChatGPT GitHub app receives read access to that personal repository.
3. Codex receives repository access so it can validate, commit, and push lasting source changes.

The ordinary ChatGPT GitHub app is read-only. A read connection is useful, but it is **not** proof that Codex can commit or push.

Personal Ops Planner can also run through Claude, an organization-approved Microsoft/VA AI environment, Gemini, or another capable runtime. Those runtimes do not have automatic feature parity. Read [`PLATFORM_PORTABILITY.md`](PLATFORM_PORTABILITY.md); the assistant must verify the exact runtime, connector actions, storage and readback instead of assuming them from a brand name.

## First — choose the deployment lane

### A. Personal browser lane

Use the GitHub template steps below. A private personal repository gives the user their own durable source lineage without local Git.

### B. Corporate, government, health-care, or locked-down lane

Open [`ENTERPRISE_PILOT.md`](ENTERPRISE_PILOT.md) before connecting anything. Do not create a personal GitHub, Google, Microsoft, Apple, or AI account to bypass workplace policy. The organization may use approved GitHub Enterprise, GitLab, Azure Repos, or a managed central source so the end user does not need a Git account.

Use synthetic or public data until the exact AI deployment, identity, data classification, storage and connector actions are approved. A website loading successfully is not approval.

### C. Portable manual lane

When connectors are blocked, the user can still use a pinned managed release plus deliberate CSV/JSON/ICS and document upload/download. This is manual portability. Do not claim unattended synchronization, scheduling or provider writes.

## Before you begin

For the personal ChatGPT/Codex lane you need:

- a web browser;
- a ChatGPT account with the GitHub app and Codex available in the product experience you use;
- a free GitHub account with a verified email address; and
- about ten minutes.

If a workplace owns your GitHub account, an administrator may need to approve ChatGPT/Codex repository access. That is an account-policy issue, not a reason to use a command line.

For another AI or an enterprise lane, replace those assumptions with the observed capability readback defined in `PLATFORM_PORTABILITY.md`. Do not require a user-owned GitHub repository when approved organization Git or managed central source is selected.

## Step 1 — Personal lane: create or sign in to GitHub

If you already have a personal GitHub account, sign in and continue to Step 2.

If not:

1. Open [GitHub sign-up](https://github.com/signup).
2. Follow GitHub's prompts and verify your email address.
3. Configure two-factor authentication when GitHub offers it.

GitHub requires a verified email for basic actions such as creating a repository. See [GitHub's account instructions](https://docs.github.com/en/account-and-profile/how-tos/account-management/creating-an-account-on-github).

Never give an assistant your GitHub password, verification code, recovery code, token, or SSH key.

## Step 2 — Personal lane: make your private personal repository

The user can create this first repository entirely on GitHub's website. An assistant may create it only when the exact runtime exposes an approved repository-creation action and verifies the resulting owner, visibility, branch and commit. Default onboarding uses GitHub's browser template flow because that capability is widely available and makes the owner/visibility choice explicit.

1. Open [Create your private copy](https://github.com/Matthew-Beare/Daily-Ops-Brief/generate). If GitHub instead shows the public starter, select **Use this template** and then **Create a new repository**.
2. Choose your own GitHub account as **Owner**.
3. Give it a neutral personal name, such as `personal-organizer`.
4. Select **Private**.
5. Leave **Include all branches** off. The default branch is the audited starter.
6. Select **Create repository from template**.

GitHub documents this browser workflow in [Creating a repository from a template](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template).

If **Use this template** is missing, stop and report: `Starter blocked — upstream is not enabled as a GitHub template.` Do not substitute a fork, Codespace, download, local copy, or command-line clone.

When GitHub finishes, copy only the non-secret repository name shown near the top, in this form:

```text
your-github-name/personal-organizer
```

Give that `owner/repository` name to the onboarding assistant. The assistant must read it back and verify the owner, private visibility, default branch, and current commit before continuing. It must never copy the reference deployment's personal data, schedules, accounts, or authority IDs.

## Step 3 — Personal ChatGPT lane: give ChatGPT read access

1. In ChatGPT, open **Settings → Apps**.
2. Find **GitHub** and select **Connect**.
3. GitHub will ask you to authorize the ChatGPT app. Select only your new personal repository unless you deliberately want broader access.
4. Return to ChatGPT.

If GitHub was already connected, open **Settings → Apps → GitHub → Choose repositories** (the wording may also be **Configure Repositories on GitHub**) and add the new repository.

New or private repositories can take about five minutes to appear. Wait once, then use the GitHub app's repository configuration page to confirm the exact repository is allowed. An organization-owned repository may show **Request** and require an administrator. See [OpenAI's GitHub connection instructions](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt).

This step proves read access only. It does not authorize commits or pushes.

## Step 4 — Personal ChatGPT lane: give Codex write access

1. Open **Codex** from ChatGPT's navigation.
2. Select **Connect to GitHub** if it is shown, and authorize the exact personal repository.
3. Create or select a Codex environment for that repository if the product asks for one.
4. Return to this onboarding conversation and provide the same `owner/repository` name.

Availability and wording can vary by ChatGPT plan or workspace. If Codex or repository authorization is unavailable, report:

```text
Source setup blocked — ChatGPT can read the repository, but no verified Codex GitHub write capability is available.
```

Do not claim installation succeeded. Do not send the user to Command Prompt as a fallback. Onboarding questions may continue, but lasting source changes remain blocked until a write-capable Codex connection is available.

## Step 5 — Required verification

Before asking life-planning questions, the assistant must show a lane-specific readback. The personal ChatGPT/Codex lane includes:

```text
Repository: owner/name
Visibility: private
Default branch: main (or the observed default)
Starter commit: observed commit ID
ChatGPT read: verified / blocked
Codex write: verified / blocked
Local command line required: no
Deployment lane: personal browser
AI runtime: observed ChatGPT/Codex deployment
Data classification: personal/public/non-sensitive
Source mode: user Git
Structured state provider: observed / blocked
Evidence provider: observed / manual / blocked
Organization approval: not applicable
Organization approval reference: not applicable
```

`Verified` means observed through the relevant connection. The existence of a button, an authorization screen, a local file, or a read-only search result is not proof of write access.

Claude and enterprise lanes replace the ChatGPT/Codex-specific fields with their exact runtime and source path. They still require capability-level read/write/readback evidence. `provider_capability_router.py` evaluates the evidence for the assistant; the user never runs it.

For corporate or regulated use, also show the exact data classification, approval status, and current approval-evidence reference. A bare approval boolean is insufficient. If approval is missing, report:

```text
Enterprise setup blocked — use synthetic/non-sensitive data until the exact AI runtime, storage, purpose and connector actions are organization-approved.
```

The first coherent personal configuration write requires the user's bounded provisioning approval. After writing, Codex must run the repository's validation and privacy gates, commit, push, read the remote commit back, and confirm CI. A failed check remains failed; it is never renamed as success.

## Step 6 — Start the personal interview

Only after the lane capability readback, open [`START_HERE.md`](START_HERE.md) in the same approved runtime. Personal ChatGPT/Codex users use the project that has access to their repository. Enterprise users use the approved organization runtime and approved source/storage lane.

The interview explicitly covers meal planning and household routines. Examples include laundry, moving a load from washer to dryer, folding/putting away, and picking up dry-cleaning, tailoring, repairs, or other dropped-off items. Those become canonical routines/tasks or Calendar reminders—not one separate ChatGPT automation per chore.

## Developer-only alternative

Local Git and command-line setup may be documented for developers elsewhere, but it is never offered during default onboarding. It may be used only after the user explicitly says they want developer/command-line mode.
