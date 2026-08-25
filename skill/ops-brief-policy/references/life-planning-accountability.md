# Life Planning, Accountability, and Study

Load this reference for personal planning, recurring routines, accountability, exercise-session organization, study/school planning, project next actions, or context-dependent home/away routines.

The purpose is to turn a user's stated goals into useful canonical state and next actions without turning chat into a shadow database or turning reminders into punishment.

## Authority and state

- Mutable goals, routines, plans, progress, study queues and next actions live in the deployment's canonical state authority, never only in chat memory.
- Reuse the existing canonical task/control/state system when it can represent the workflow cleanly. Provision an additional routine/plan/study table only during approved setup when the selected module genuinely needs fields that the existing schema cannot safely hold.
- Preserve completion, misses, removals and revisions as history according to the deployment's retention rules. Do not infer completion from silence.
- Documents, syllabi, manuals and source material remain in canonical document/evidence storage with links from mutable state rather than being duplicated into prompts.
- Calendar is an optional projection; it is not the canonical routine/study database.

## Adaptive intake

Ask no more than four related questions at a time. Capture only fields that change behavior.

For any selected goal/routine identify:
- purpose/outcome;
- frequency or real deadline;
- preferred windows and context modes;
- normal time budget and optional component blocks;
- equipment/resources/dependencies;
- minimum viable next action or session;
- completion definition;
- check-in/anti-nag behavior;
- miss/reschedule policy;
- progression/review rule when relevant.

If the user works away from home, explicitly distinguish what can happen HOME versus ROAD/TRUCK/FIELD/other configured context. Do not assume an away version exists merely because the user travels.

## Next-action planner

When asked what to do next:
1. read canonical open state and verified deadlines;
2. exclude Done/Removed/cancelled work and context-incompatible actions;
3. honor prerequisites and blocks;
4. rank by real deadline/impact/priority using the user's selected model;
5. choose the smallest actionable next step that fits the current supported context and available time when known;
6. offer a minimum viable version when an active routine allows one;
7. keep unavailable-context work in backlog rather than presenting it as immediately actionable.

Never manufacture urgency, deadlines, completion or hidden priorities.

## Routine accountability

Accountability is evidence tracking plus useful prompting, not scolding.

- Before a planned session, surface the agreed next action or component list at the configured time/cadence.
- On explicit completion, record the supported completion evidence.
- On partial completion, record partial rather than promoting it to complete.
- On a miss, follow the selected policy: reschedule, reduce scope, ask one blocker question, or continue next cycle.
- Once a reminder/check-in has been acknowledged, obey the user's anti-nag rule.
- Review consistency/progression only at the selected cadence or when requested.
- Adjust the plan only from user-supported evidence; never rewrite goals merely because a scheduled check produced no response.

## Exercise / fitness organization

This module organizes a user-selected routine. It does not diagnose health conditions or invent medical constraints.

A session may contain user-defined blocks such as cardio, strength, mobility/stretching, yoga, warm-up/cool-down, or another component. Store component duration/sets/reps/load/variation only when the user wants that level of tracking.

Progression may use evidence such as:
- completion consistency;
- duration;
- repetitions/sets;
- load;
- exercise variation;
- user-defined yoga/mobility skill or sequence progression.

When the user has HOME/away modes, support separate equipment/resource versions while preserving one underlying goal. Do not silently treat an abbreviated away session as a failed home session if the user defined it as a valid variant.

Do not invent injury restrictions, diagnoses, calorie targets, medication advice or unsafe progression. If the user supplies a health/safety constraint, treat it as a constraint and do not reinterpret it medically.

## School / study workflow

For selected education tracks preserve:
- program/course/certification identity;
- source links for syllabus/materials;
- verified assignments/exams/projects/deadlines;
- status and prerequisites;
- weekly target and preferred session size;
- HOME/away applicability;
- offline/download requirements when relevant;
- accountability cadence;
- optional Calendar Projection behavior.

Study next-action order:
1. verified imminent deadlines and prerequisites;
2. work already in progress that can be completed efficiently;
3. prerequisite learning that unlocks upcoming work;
4. short compatible work for constrained windows;
5. backlog items that are appropriate but not urgent.

The assistant may explain concepts, quiz, summarize user-provided material, create study plans, review the user's work, and help decompose assignments. Never fabricate submissions, attendance, grades, citations or proof of work. Do not encourage academic dishonesty.

## Projects and long-term goals

Keep active commitments distinct from someday/backlog ideas. An active project should have an outcome, current state, next milestone, blockers/dependencies, context restrictions and a next action. Remove stale project clutter from normal briefs unless the user's review cadence makes it relevant.

## Brief integration

Only surface accountability/study/project content when it creates a useful decision or reminder:
- a session is due in its configured window;
- a verified deadline approaches;
- a planned action is blocked and needs a decision;
- a review/progression checkpoint is due;
- the user explicitly asks for the next action.

Do not dump every routine, course and project into every brief. Context mode may change what is actionable, but it never changes the canonical scheduling timezone.

## Calendar projection

When the user opts in, routine sessions, study blocks and verified deadlines may project to Calendar through the normal Calendar Projection identity/dedupe rules. Revisions update the linked event. Never create a separate automation per routine/session and never invite attendees without separate authority.

## Failure/recovery

A failed reminder/scheduler does not erase routine/study state. Preserve canonical progress and use the Module Circuit Breaker Report for repeated scheduler/connector failures. Resume from canonical state after repair; never reconstruct history from what the assistant remembers saying.
