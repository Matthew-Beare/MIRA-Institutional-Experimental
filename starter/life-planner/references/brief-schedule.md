# User-owned brief schedule

M.I.R.R.O.R. has **no stock brief time**. Never inherit another deployment's schedule, timezone, AM/PM labels, or delivery cadence.

## First boot

When recurring briefs are available, ask the user whether they want them. If yes, ask for the exact local time of each brief and the canonical IANA timezone. The user may choose one slot, several slots, custom names, or no recurring briefs at all.

Write only those explicit choices into that deployment's non-secret version-controlled configuration. Validate the schedule with `scripts/brief_schedule.py`, commit and push the coherent configuration checkpoint under the deployment's standing source-write authorization, read the remote commit back, and require green CI before provisioning or changing the live scheduler.

The scheduler is a projection of the Git configuration. It is not the source of truth.

## Change contract

When the user later says to move, add, disable, rename, or remove a brief:

1. read the current version-controlled schedule;
2. apply only the requested change;
3. validate the resulting schedule;
4. commit and push the config change and read the remote commit back;
5. reconcile the live scheduler to exactly that configuration;
6. read the scheduler definition back and compare timezone, enabled slot IDs, local times, and notification modes;
7. require one observed firing before calling a newly changed recurring schedule fully proven.

Do not silently edit only the provider scheduler. Do not leave Git describing an old schedule after the live scheduler changed. Routine mutable life state still belongs in the canonical state authority; the schedule is durable behavior/configuration and therefore belongs in source control.

## Provider limitations

Use the fewest scheduler objects the selected provider can truthfully support. If one provider object cannot represent all requested local slots without creating extra unintended firings, use the minimum provider-supported decomposition while preserving one logical M.I.R.R.O.R. control-cycle service. Record that implementation detail in the Integration Registry. Never change the user's requested times merely to fit a provider shortcut.

## Manual smoke test

A manual brief smoke test is separate from scheduler evidence. It may run at any wall-clock time and should exercise the same current policy, authorities, reconciliation, and rendering path. It must carry a manual Run ID and must not claim that any configured recurring slot fired.
