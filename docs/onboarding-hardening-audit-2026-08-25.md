# Non-technical onboarding hardening audit — 2026-08-25

## Outcome

The Foodie failure was reproducible from the repository contract: the front door called itself non-technical while the next documents told the assistant to `fork/clone`, pin Git history, run CI, commit, and push. There was no installation state machine, no hard prohibition on local tooling, and no distinction between the read-only ChatGPT GitHub app and a write-capable Codex repository connection. The assistant therefore had room to choose Command Prompt as an implementation path.

The repository now defines one default browser-only path and fails closed when a capability is absent.

## Root-cause evidence

Before this change:

- `starter/START_HERE.md` said the user should not need Git jargon but immediately supplied a large engineering/provisioning prompt;
- `starter/README.md`, `starter/VERSIONING.md`, `starter/DEPENDENCIES.md`, and `starter/PERSONAL_FORK_LIFECYCLE.md` used `fork/clone` or equivalent language;
- no document required the assistant to prove repository owner, visibility, branch, commit, read access, and write access before interviewing or provisioning;
- no CI test rejected Command Prompt, GitHub CLI, local clone, Codespace, token, or SSH-key fallbacks; and
- the contract treated “GitHub connected” as one condition even though OpenAI documents the ordinary ChatGPT GitHub app as read-only.

This was a specification defect, not Foodie's mistake.

## Repaired default flow

`starter/INSTALL.md` and `starter/install-flow.json` now require:

1. a GitHub account with verified email;
2. one private personal repository created through GitHub's browser template UI;
3. exact `owner/repository` readback including visibility, default branch, and observed commit;
4. separately verified ChatGPT GitHub read access;
5. separately verified Codex GitHub write access;
6. no local command line for the non-technical path; and
7. validation, commit, push, remote readback, and CI after bounded initial provisioning.

If the template switch, repository access, organization approval, or Codex write capability is missing, setup reports one precise blocked state. It does not invent success and does not route the user to local tooling.

## Template-versus-fork decision

The private default uses a GitHub template rather than a fork. This lets a user create a private independent repository in the browser and avoids copying deployment state. GitHub templates begin with a new repository history, so the deployment must record the exact upstream commit/tree as provenance and apply future audited releases deliberately; it must not assume a normal fork merge base exists.

The upstream repository must have GitHub's **Template repository** setting enabled. This is a live provider gate, not something CI can prove. At audit time, the connected GitHub repository tools could commit files but did not expose repository-settings mutation. The cloud browser reached GitHub signed out, so the setting still requires authenticated GitHub readback before the installer can be called fully live-ready.

## Feature discovery changes

- Meal planning remains a current requirement and a first-boot question. Its manifest remains honestly `contract-only`; the repository does not claim an executable planner that does not exist.
- Household routine service selection is now machine-readable.
- The question bank explicitly covers laundry start, washer-to-dryer transfer, drying, folding/putting away, and clothing/other service pickup.
- Household routine delivery is constrained to canonical task/routine state plus a consolidated brief or Calendar projection. It cannot spawn one ChatGPT Scheduled Task per chore.
- Routine ownership is never inferred from household membership.

## Naming boundary

The public working name is now **Personal Ops Planner**. `Life Planner` was rejected as an automatic replacement because it is already used by current organizer products, while `LifeOS` is also actively used by multiple products. The working name is descriptive and is not represented as completed trademark clearance.

`LyfeOS Control Cycle` may remain temporarily as a reference-deployment compatibility identifier. Renaming a live scheduler/provider object requires an atomic provider migration, readback, rollback plan, and observed firing; a cosmetic source-only rename would create drift.

## Regression evidence

`starter/tests/test_nontechnical_installation.py` verifies:

- the browser-only entry point and no-terminal wording;
- the private GitHub template path;
- independent read/write capability gates;
- the required repository readback;
- meal/laundry/pickup discovery; and
- the current public working name.

`starter/tests/test_onboarding_profile_router.py` verifies the household-routine service, reminder examples, no-per-chore scheduler rule, and no ownership inference.

The generated feature catalog now includes the installer, independent read/write gates, and household laundry/pickup contract. Repository-wide validation, privacy/history audit, full test suites, remote push readback, GitHub template readback, and GitHub Actions remain release gates.
