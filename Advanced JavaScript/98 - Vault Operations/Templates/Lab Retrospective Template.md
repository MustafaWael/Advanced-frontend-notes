---
tags: [template]
module: "98 - Vault Operations"
priority: important
status: solid
---

# Lab Retrospective Template

Fill this in within a day of finishing a [[90 - Labs/00 - Labs MOC|lab]] — the mispredictions evaporate fast, and they're the valuable part. Copy below the divider.

---

```markdown
---
tags: [lab-retrospective]
module: "90 - Labs"
priority: important
status: solid
date: YYYY-MM-DD
lab: "[[90 - Labs/01 - Event Loop and Rendering Profiler Lab|WHICH LAB]]"
---

# Retrospective: LAB NAME

## Acceptance Criteria Honesty Check

Which criteria passed on the first try, which took iterations, which did I quietly soften?

## Mispredictions

Things that did NOT behave as I expected, each with the mechanism I now understand:

1. Predicted X, observed Y, because MECHANISM ([[99 - Glossary|link the owning note]]).

## The Planted Bugs

For each debugging task: how the symptom actually presented, and what diagnostic step found it fastest.
Would I have found it in production, where I didn't plant it?

## What the Tests Caught (and Didn't)

Which of my tests failed usefully during development? What bug slipped past all of them, and which layer should own it ([[24 - Testing and Quality/01 - Testing Mental Model|mental model]])?

## Accessibility Findings

What the keyboard/screen-reader pass found that the code review didn't ([[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|manual checks]]).

## Answers I'd Give Differently Now

Re-answer one interview question from the lab brief — the before/after of my own answer.

## Follow-ups

- [ ] Vault notes to improve or cross-link based on what I learned:
- [ ] A debugging incident worth writing up separately:
```
