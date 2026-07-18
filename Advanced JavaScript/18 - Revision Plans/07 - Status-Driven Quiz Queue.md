---
tags: [revision, quiz, workflow, interview]
module: "18 - Revision Plans"
priority: important
status: not-started
aliases: [quiz pool, weekly quiz queue]
---

# Status-Driven Quiz Queue

## Maturity Target

- Priority: #important
- Study time: 15 minutes to set up; used weekly thereafter
- Interview signal: none directly — this is the operating system that decides *what* gets drilled.
- Production signal: your `status` frontmatter stops being decoration and starts driving what you practice.
- Fast track: open the Quiz Pool view in [[Base.base|Base]], pick the top 5, quiz.

## The Idea

The vault already tracks two signals on every note: `priority` (how much interviews care) and `status` (how much *you* have it). The quiz queue is their intersection, drilled in priority order:

| Tier | Definition | Treatment |
| --- | --- | --- |
| 1 | `status: learning` + `priority: must-know` | **This week's quiz pool.** Drill until promoted. |
| 2 | `status: learning` + `priority: important` | Next up once Tier 1 is under ~5 notes. |
| 3 | `status: not-started` + `priority: must-know` | Intake: study first, then it enters Tier 1. |
| 4 | `status: solid` (any priority) | Spot-check one per week; demote honestly on a miss. |

The Base views implement this: **Quiz Pool** in `Base.base` is Tier 1 exactly (learning + must-know, MOCs and checklists excluded); **Study Queue** is all `learning`; **Must Know** is Tiers 1+3 combined.

## The Weekly Loop

1. **Monday** — open Quiz Pool. Pick at most 5 notes (fewer, drilled harder, beats many skimmed). These are the week's pool; write them in your weekly review note ([[98 - Vault Operations/Templates/Weekly Review Template|template]]).
2. **During coaching sessions** — quiz questions come from the pool first. One question at a time, answer before reveal, graded against the mature bar: definition → mechanism → trace → production bug → safe fix with tradeoff → short + deep answers.
3. **Promotion rule** — a note moves `learning → solid` only after **two clean quiz passes in separate sessions** (spacing is the point — one pass measures recognition, the second measures retention).
4. **Demotion rule** — miss the mechanism on a `solid` spot-check and it goes back to `learning` the same day. No negotiation; the queue only works if status is honest.
5. **Friday** — status updates written, next week's candidates noted. If Tier 1 is empty: pull from Tier 3 (study new must-knows) rather than Tier 2 — coverage of must-knows beats depth on importants.

> [!tip] Coaching hook: at the start of a quiz session, say "quiz me from the pool." The pool being small and explicit is what makes grading against the bar possible — an unbounded "quiz me on JavaScript" session always regresses to comfortable topics.

> [!warning] The failure mode this note exists to prevent: `status` values that drift from reality — notes marked `learning` for months with no drills, or optimistic `solid`s that were one lucky recall. If the Quiz Pool view has more than ~10 rows, the statuses are stale, not the plan ambitious. Fix the statuses first.

## Related Notes

- [[18 - Revision Plans/00 - Revision Plans MOC|Revision Plans MOC]]
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
- [[98 - Vault Operations/Templates/Weekly Review Template|Weekly Review Template]]
- [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]
