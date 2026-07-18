# Front End System Design — Comprehensive Study Plan

> Primary source: [GreatFrontEnd Front End System Design Playbook](https://www.greatfrontend.com/front-end-system-design-playbook)
> Learned notes: `progress/greatfrontend/`
> Target: mid-level frontend interviews. Created 2026-07-17.

## Goal

Be able to take any vague front-end system design prompt (application or UI component) and deliver a structured 45–60 min answer using the RADIO framework, with strong tradeoff narration and deep dives matched to the product category.

## Phase 1 — Foundations (Week 1)

Master the theory before touching questions.

1. Read `progress/greatfrontend/knowledge_base/01_introduction.md` — understand FE vs BE system design, what interviewers do NOT want (capacity estimation, DB schemas, load balancers).
2. Read `02_types_of_questions.md` — memorize the two question types and the topic-per-app-category table.
3. Study `03_radio_framework.md` deeply — this is the backbone. Memorize the 5 steps, their time budgets (10/20/10/20/40), and the typical client architecture (View / Store / Data access / Server-as-black-box).
4. Read `04_evaluation_criteria.md` and `05_common_mistakes.md` — know how you're scored and the 6 pitfalls.
5. Drill `06_cheatsheet.md` until you can reproduce it from memory.

**Checkpoint:** explain RADIO out loud in 5 minutes without notes.

## Phase 2 — Case studies (Week 2)

Learn one worked example of each question type.

1. `progress/greatfrontend/questions/01 - News Feed (Facebook).md` — the canonical *application* question. Focus: cursor vs offset pagination, store normalization, CSR vs SSR reasoning, optimistic updates, virtualization.
2. `progress/greatfrontend/questions/02 - Autocomplete.md` — the canonical *UI component* question. Focus: props API design, debouncing, race conditions, cache design, ARIA combobox pattern.
3. Re-do both from scratch on Excalidraw (blank canvas, 45-min timer) and compare with the notes.

**Checkpoint:** both case studies re-derived solo within 45 min each.

## Phase 3 — Supporting knowledge (Weeks 2–3, in parallel)

Deep-dive topics that recur in the O step — cross-link with the Advanced JavaScript module:

- Networking: HTTP caching, WebSockets vs SSE vs long polling (`Advanced JavaScript/20 - Network and Security`)
- Rendering & performance: render pipeline, virtualization, observers (`19 - DOM and Browser APIs`)
- State architecture: state taxonomy, server state, app architectures (`28 - Frameworks and Application Architecture`)
- Accessibility patterns: combobox, dialog, menu (ARIA APG)
- Rendering strategies: CSR vs SSR vs SSG vs ISR, hydration
- Offline & storage: Service Workers, IndexedDB, optimistic UI

## Phase 4 — Breadth practice (Weeks 3–5)

Practice one question per session (45 min, Excalidraw, out loud), then write notes to `progress/greatfrontend/questions/`. Suggested order (free → representative premium prompts, solved solo):

1. Modal Dialog (component, a11y-heavy)
2. Dropdown Menu (component, a11y-heavy)
3. Image Carousel (component, performance)
4. Data Table (component, large data)
5. E-commerce (app, SEO/performance)
6. Chat App (app, real-time)
7. Photo Sharing (app, media upload)
8. Video Streaming (app, streaming)
9. Google Docs (app, collaboration/conflict resolution)
10. Pinterest (app, layout/media)

## Phase 5 — Mock interviews (Week 6)

- 2–3 full mocks with a peer or AI interviewer; record and self-review against the 6 evaluation axes.
- Grade every mock on: problem exploration, architecture, technical proficiency, tradeoffs, product/UX sense, communication.
- Re-drill weak axes.

## Session rules (always)

- Never start designing before clarifying scope (functional + non-functional requirements).
- Write RADIO on the board; check letters off.
- Verbalize every tradeoff — silent reasoning scores zero.
- 2–3 alternatives per decision, then recommend one for THIS context.
- No buzzwords you can't defend.
- Match deep dives to product category; skip framework debates, tooling, CI/CD.

## Progress tracking

Log each studied source under `progress/<source-name>/`. Current sources: `greatfrontend` (guides ✅, News Feed ✅, Autocomplete ✅, 18 premium questions pending self-solve).
