# Personal Ops Planner Interview Ledger and Fail-Forward Interview

The adaptive interview is a **durable workflow**, not a single uninterrupted chat. A user may change subjects, ask for immediate help, close the app, or return later. Personal Ops Planner must preserve interview progress in the canonical structured state authority and continue without restarting or silently abandoning discovery.

## Ledger

First boot creates an `Interview Ledger` table in the selected structured state store. One row exists per question ID across every installed question bank. `questions.json` is the core bank; versioned extension banks such as `questions.profile-and-stock-services.json` merge into the same ledger and must use globally unique IDs.

Minimum fields:

- Question ID
- Question Bank
- Section ID
- Prompt Version
- Status
- Answer / Resolution Summary
- Evidence Source IDs
- Applies / Not-Applicable Reason
- Asked At
- Resolved At
- Deferred Until
- Confidence
- Last Reviewed

Allowed status values:

- `Unresolved`
- `Asked`
- `Answered`
- `Resolved from evidence`
- `Not applicable`
- `Deferred`

An interview is complete only when every question in every installed question-bank version has a terminal resolution of `Answered`, `Resolved from evidence`, or `Not applicable`. `Deferred` and `Unresolved` remain open.

This does **not** mean asking every prompt verbatim. Evidence can resolve questions, and branch logic can mark questions not applicable. The point is complete coverage, not 100-question punishment.

## Fail-forward conversation rule

At every user turn during incomplete onboarding:

1. answer the user's immediate request normally;
2. update any interview rows that the turn resolved incidentally;
3. inspect the next unresolved applicable questions;
4. when conversationally reasonable, end with **one** next interview question, or one tightly related batch of at most four;
5. if the user diverts again, follow the diversion and repeat the process;
6. never pretend onboarding is complete while open ledger rows remain.

Do not prefix every response with setup bureaucracy. The reminder belongs at the end after the user's current need is handled.

## Anti-annoyance controls

If the user says `not now`, `later`, `skip this for now`, or equivalent:

- set that row to `Deferred`;
- store an explicit revisit time/cadence when supplied;
- otherwise revisit after meaningful progress in other sections, not on every turn.

If a user repeatedly defers the same topic, summarize why it matters and offer a compact choice such as `answer now / not applicable / defer`, rather than repeating the full prompt.

Never mark `Not applicable` merely because the user ignored a question.

## Evidence-first resolution

Before asking a factual question, search permitted current evidence and connected authorities. If evidence resolves it with adequate confidence:

- record `Resolved from evidence`;
- store the supporting source identifier/provenance;
- only ask for confirmation when the fact is ambiguous, sensitive, contradictory, or materially affects permissions/safety.

Preferences and consent are not silently inferred from evidence. For example, discovering recipes does not imply permission to enable meal planning or the stock recipe-library service.

## Question-bank upgrades

When any installed question bank changes:

1. compare installed bank/version/question IDs with the ledger;
2. reject duplicate IDs across banks;
3. add rows for new question IDs as `Unresolved`;
4. retain prior answers for unchanged IDs;
5. reopen a question only when the new version materially changes its meaning or a dependent policy requires reconfirmation;
6. preserve provenance/history rather than wiping the interview and starting over.

Removing or disabling an extension bank does not delete its historical answers. Mark no-longer-installed rows inactive in the ledger while preserving provenance.

## Completion handoff

When no open applicable rows remain across all installed banks, produce a compact final setup summary and mark onboarding complete in canonical state. Future feature additions may add new interview rows without invalidating completed unrelated sections.
