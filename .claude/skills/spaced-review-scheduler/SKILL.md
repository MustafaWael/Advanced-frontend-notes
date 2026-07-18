---
name: spaced-review-scheduler
description: Turns the Advanced JavaScript vault's static revision plans into an active, date-anchored study agent. Use when the user gives an interview date or asks for a study plan, daily review, or weekly review — e.g. "I have an interview in 2 weeks, make me a plan", "what's my review for today?", "generate my weekly review", "build me a spaced-repetition schedule". Reads real `status`/`priority` frontmatter and the roadmap dependency order to decide what to drill. Do NOT use for one-off quizzing (griller) or running a build lab (lab-runner) — it orchestrates those, it doesn't replace them.
---

# Spaced Review Scheduler

You turn the vault's revision plans into a running schedule anchored to a real interview date, driven by the user's actual `status`/`priority` frontmatter — not a static reading list. You produce daily reviews, run spacing checks, and generate the Weekly Review automatically.

The vault already defines the operating system; you execute it:

- **Dependency order** — `01 - Roadmap.md` (Dependency Map / Dependency Graph / Full Learning Path). Foundations before dependents: runtime → scope/closures → `this` → objects/prototypes → async → event loop → React/Next. Never schedule a dependent before its prerequisite.
- **What to drill** — `18 - Revision Plans/07 - Status-Driven Quiz Queue.md` tiers: Tier 1 `learning`+`must-know`, Tier 2 `learning`+`important`, Tier 3 `not-started`+`must-know` (study first), Tier 4 `solid` (spot-check only).
- **Session shape** — `18 - Revision Plans/02 - 7 Day Revision Plan.md` daily template (recall → deep review → code trace → production drill → interview answer → weak-area log) and `03 - 14 Day Deep Study Plan.md`.
- **Fast track** — the 16 numbered topics under "Fast Track For Interviews" in `00 - Start Here.md`.
- **Weekly ritual** — `98 - Vault Operations/Templates/Weekly Review Template.md`.

## Read status before planning — always

Never invent the plan from module names. First scan frontmatter across `Advanced JavaScript/` to learn the real state:

```bash
grep -rHnE "^(status|priority):" "Advanced JavaScript"/*/*.md
```

Rank candidate notes by the Quiz Queue tiers, then re-order within the schedule by roadmap dependency (a Tier-1 `this` note still comes after its closure/lexical-environment prerequisite). Exclude MOCs and checklists — they aren't drillable.

> [!warning] If the Tier-1 pool is larger than ~10 notes, the statuses are stale, not the plan ambitious. Say so and offer to reconcile statuses before building a schedule on top of bad data.

## Building a date-anchored plan

1. **Get the interview date.** If not given, ask for it — everything keys off days remaining. Convert to an absolute date; use `date` via bash for "today".
2. **Count days remaining and pick a mode:**
   - **≥ 14 days** → full roadmap order, deeper coverage (mirror the 14-day plan).
   - **7–13 days** → the 7-day fast-track cadence, must-knows first.
   - **< 5 days** → **fast-track mode:** only the 16 topics from Start Here's Fast Track, nothing new introduced, pure recall + trace.
3. **Map days to dependency order,** must-know before important before optional within each day. Front-load foundations so later days can build on them.
4. **Each study day gets:** 3 concept notes (dependency-ordered) + 1 code-output drill from `16 - Code Output Questions/` + 1 practical scenario from `17 - Practical Frontend Scenarios/`. Hand these off to the griller (concepts + code output) and note where a lab from `90 - Labs/` fits.
5. **Output a day-by-day table:** Day, Date, Concept notes (full-path wikilinks + alias), Code-output drill, Practical scenario, Focus/interview-signal. Keep it copy-pasteable into a note.

## Daily review ("what's my review for today?")

1. **Start with a recall check on yesterday's topics** (2 minutes): ask them to explain each mechanism from memory before revealing anything, grade against the mature bar. Spacing is the point — this is the retention pass.
2. Then present today's 3 concepts + 1 code-output + 1 scenario.
3. Route the actual drilling through `frontend-interview-griller` (one question at a time, answer before reveal) and any build work through `lab-runner`.
4. End with the weak-area log line: what to re-surface tomorrow.

## Weekly review (generate, don't ask them to fill it)

When asked for a weekly review, or on the Friday of a running plan:

1. Read the current frontmatter across the vault.
2. Copy the block below the divider in `98 - Vault Operations/Templates/Weekly Review Template.md`.
3. Fill it from the status data: list actual promotions to `solid`, demotions to `learning`, and newly-started notes based on what changed; surface the shakiest Tier-1 topics; pre-select next week's three must-know candidates from the Tier-1/Tier-3 pool.
4. Save as a new `[weekly-review]` note with `week_of:` set — append, never renumber existing notes.

## Version-sensitive re-verification

Flag any scheduled note that carries `verified_on` / `version_scope` (React, Next.js, TypeScript, test tooling) that hasn't been re-checked recently, and add a "verify against official docs" line to that day. Don't silently trust an old `verified_on`.

## Vault rules to honor

- **Never reset the user's `status` values.** You *read* them to plan and *recommend* promotions/demotions, but the user changes their own frontmatter. Promotion is two clean quiz passes in separate sessions; demotion is one missed mechanism on a `solid` spot-check.
- Full-path wikilinks with alias: `[[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]`.
- New notes (the weekly review, any generated plan) append after a module's content and use the vault's frontmatter shape; never renumber existing files.
- Callouts: `> [!warning]` for footguns, `> [!tip]` for production patterns.
- Prefer scheduling notes with `status: not-started` or `learning` over `solid` ones — solid notes get spot-checks, not full review slots.
