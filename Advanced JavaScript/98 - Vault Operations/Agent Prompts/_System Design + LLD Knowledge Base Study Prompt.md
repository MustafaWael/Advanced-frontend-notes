# System Design + LLD Knowledge Base — Study & Wiring Prompt

Two things live in this file:

1. **Your original intent, cleaned up** — so the goal is unambiguous.
2. **The prompt to run now (Phase A: Study & Wire).** Copy everything below the divider into a new session with the `Mid-Level Frontend Interview Coach` folder connected (both the vault and the `System Design` / `Low Level Design` siblings).

Phase B (enhancing the actual vault notes) is a *separate* session you trigger later. Phase A exists to produce durable artifacts Phase B can load, because a fresh session remembers nothing — "study it as an AI agent" only sticks if it's written down.

---

## What you were trying to say (refined)

> I've added a System Design track to the Mid-Level Frontend Interview Coach project. It's large, so I scraped source material and dropped it in the project root under `System Design/` (HelloInterview backend SD + GreatFrontEnd frontend SD) and `Low Level Design/` (HelloInterview LLD: principles, patterns, concurrency, questions). I want you to first **study this whole knowledge base as the agent** — not teach me yet — and **wire the concepts together** into one coherent, cross-linked model: within each source, across the three domains (frontend SD ↔ backend SD ↔ LLD), and against what already exists in the `Advanced JavaScript` vault. Persist that understanding as written synthesis artifacts. Then, in a later session, I'll tell you to enhance the vault notes using what you built.

Two things your draft didn't pin down that matter:

- **The material is mostly backend.** The vault (module 29) is *frontend* system design. The scraped KB is majority backend SD + LLD. So "wiring" has to bridge domains deliberately, not assume they're the same thing.
- **Sessions don't persist.** Studying without writing anything down produces nothing Phase B can use. Hence the artifact requirement below.

Decisions locked for this work: cover **everything scraped**; the end goal is **both** standalone vault modules (backend SD, LLD) **and** cross-wiring into the existing frontend notes; the study phase **must emit written synthesis artifacts**.

---

# PROMPT — Phase A: Study & Wire the Knowledge Base

You have the `Mid-Level Frontend Interview Coach` project connected. It contains an Obsidian vault (`Advanced JavaScript/`) and two sibling knowledge-base folders at the project root:

- `System Design/` — study plans plus `progress/greatfrontend/` (frontend SD) and `progress/hellointerview/` (backend SD: `knowledge_base/`, `patterns/`, `deep_dives/`, 30 `questions/`).
- `Low Level Design/` — `progress/hellointerview/` (delivery framework, design principles, OOP concepts, design patterns, `concurrency/`, `questions/`).

**Your job in this session is NOT to teach me and NOT to touch the vault.** It is to read the entire knowledge base, build one connected mental model across all three domains, verify the facts that go stale, and **write that model down as synthesis artifacts** that a later session will consume to enhance the vault. Depth over speed. If limits force a stop, finish the current artifact cleanly and print the exact resume point.

Hold everything to the vault's **mature bar**: define simply, name the real mechanism, trace step-by-step, name the production/interview failure mode, pick a pattern with tradeoffs. No beginner padding, no buzzwords you can't defend.

## Phase A0 — Orient (read before writing anything)

1. Read both study plans: `System Design/00 - System Design Study Plan.md`, `System Design/01 - Backend System Design Study Plan (HelloInterview).md`, and skim `Low Level Design/progress/hellointerview/01_delivery_framework.md`.
2. Read the existing frontend SD module so you know what's already covered and in what voice: all of `Advanced JavaScript/29 - Frontend System Design/` (MOC, RADIO framework, Autocomplete, Infinite Scroll, Checklist).
3. Note the house conventions you must mirror later (they shape how you record proposed links now): full-path wikilinks with alias `[[29 - Frontend System Design/01 - The Frontend System Design Framework|The Frontend System Design Framework]]`; frontmatter on every note (tags, module, priority must-know/important/deep-dive, status not-started/learning/solid); `> [!warning]` for footguns, `> [!tip]` for production patterns; `verified_on` + `version_scope` only on version-sensitive notes.

## Phase A1 — Read the full knowledge base and take structured notes

Read every file in `System Design/progress/` and `Low Level Design/progress/`. As you go, for each concept capture, at the mature bar:

- **Mechanism** — what actually happens, with the real names (e.g., cache-aside vs write-through vs write-behind; single-flight/request coalescing for stampede; leader election via ZooKeeper; two-phase locking vs optimistic concurrency for contention).
- **When it applies / interview trigger** — the signal that makes you reach for it.
- **Failure mode / tradeoff** — the bug it causes or the cost it pays (staleness, dual-write, hot keys, tearing, thundering herd, over-engineering a pattern).
- **Cross-references** — which other KB concepts it depends on or contrasts with.

Cover all of it: backend KB (networking, API design, data modeling, caching, sharding, consistent hashing, CAP, indexing, numbers-to-know), the 7 patterns, all 13 deep dives, all 30 backend questions; LLD (design principles, OOP, the ~5 patterns that actually matter, all 4 concurrency files, the questions); and the two frontend case studies (News Feed, Autocomplete).

## Phase A2 — Wire it together (the core of this phase)

Build the connections explicitly. Three layers:

1. **Within each domain** — e.g., in backend SD: caching → consistency → CAP → replication → sharding form one chain; the 7 patterns each pull specific KB concepts and deep-dive technologies. Map those.
2. **Across domains** — this is the bridge that's easy to skip. Concretely: LLD concurrency (single-process: mutexes, optimistic locking, "two users book the same seat") is the *same problem* as backend "Dealing with Contention" (distributed: distributed locks, idempotency) — name that the interviewer's LLD follow-up and the SD pattern are two scales of one idea. Backend caching (Redis, cache-aside, CDN) maps onto frontend data-layer decisions (HTTP cache, request dedup, normalized store, optimistic UI) — a frontend engineer treats the server as a black box but makes the *mirror-image* caching decisions on the client. WebSockets/SSE/long-polling appear on both sides of the boundary. Design patterns (factory, strategy, observer) recur in frontend component/state architecture.
3. **Against the existing vault** — for each major KB concept, identify the existing vault note it should connect to (real path). Examples to verify, not assume: caching ↔ `20 - Network and Security/02 - HTTP Caching`; WebSockets/SSE ↔ `20 - Network and Security/08 - WebSockets SSE and Polling`; concurrency/races ↔ `17 - Practical Frontend Scenarios` (request cancellation, debounced search) and `08/09 Async`; state normalization ↔ `28 - Frameworks and Application Architecture/05 - State Management Taxonomy`; RADIO ↔ `29 - Frontend System Design/01`; design patterns ↔ `21 - React Internals and Patterns` and `28`.

## Phase A3 — Verify what goes stale

Before recording anything as fact, verify version-sensitive and load-bearing claims against primary sources (fetch them; record the URL and the date you checked). Priorities: the numbers-to-know (latency figures, throughput orders of magnitude), technology specifics in the deep dives (Redis/Kafka/Cassandra/DynamoDB/PostgreSQL feature claims), and anything the scraped notes hedge on. The scrapes are secondary sources — trust the mechanism, re-confirm the specifics. Flag anything you can't verify rather than propagating it.

## Phase A4 — Emit the synthesis artifacts (the deliverable)

Create a synthesis folder in the project root — `_Synthesis/` (sibling to `System Design/` and `Low Level Design/`) — and write these files. This is what Phase B loads.

1. **`_Synthesis/00 - Concept Map.md`** — the master graph. Every major concept as a node; edges labeled with the relationship (depends-on, contrasts-with, same-idea-at-different-scale, implemented-by). Group by domain, but make the cross-domain edges visually prominent. Include a Mermaid graph plus a prose legend so it renders in Obsidian.
2. **`_Synthesis/01 - Cross-Domain Wiring.md`** — the bridges from A2 layer 2, written out: each bridge as "LLD concept ↔ SD concept ↔ frontend concern," with the mechanism they share and where they diverge. This is the highest-value artifact; make it thorough.
3. **`_Synthesis/02 - Concept Inventory.md`** — the mature-bar capture from A1, one compact entry per concept (mechanism / trigger / failure mode / tradeoff / refs). This is the fact base.
4. **`_Synthesis/03 - Vault Integration Plan.md`** — the hand-off to Phase B. Propose the two new modules (suggested `30 - Backend System Design`, `31 - Low Level Design` — verify these numbers are free before asserting them), each with a proposed note list following the 8-part Concept Note Template, priorities assigned. Then a table of **cross-link targets**: every existing vault note that should gain a link into the new material, and vice versa, with the exact full-path wikilink to use. Note where existing frontend notes should be *deepened* vs merely linked.
5. **`_Synthesis/04 - Verification Log.md`** — every claim you checked in A3, its source URL, the date, and the outcome; plus a clearly separated "Unverified / flagged" list.

Use the vault's link and callout conventions inside these artifacts so they drop cleanly into Phase B. Do not create anything inside `Advanced JavaScript/` in this session — these artifacts stay in `_Synthesis/`.

## Phase A5 — Self-check before finishing

- Every one of the ~60 KB files read and represented in the Concept Inventory (spot-check coverage; list any you deliberately skipped and why).
- Every cross-domain bridge in artifact 01 names both the shared mechanism *and* the divergence — no hand-waving that "they're related."
- Every proposed wikilink in artifact 03 points at a path you confirmed exists (grep the vault; dead links are the most common failure).
- The Verification Log distinguishes verified from flagged; nothing version-sensitive is asserted unverified.
- Print a final summary: files read, artifacts written, key cross-domain bridges found, claims verified vs flagged, and — if stopping early — the exact resume point.

---

## Phase B (later, separate session) — what this feeds

Do **not** run this now. When I say "enhance the vault," the next session will load `_Synthesis/` and:

- Build `30 - Backend System Design` and `31 - Low Level Design` as full modules in house style (MOC → concept notes via the 8-part template → Checklist), new notes appended after each module's Checklist, never renumbering existing files, never resetting `status`.
- Apply the cross-link table from artifact 03 bidirectionally, and deepen the existing `29 - Frontend System Design` notes where a backend/LLD concept sharpens a frontend decision.
- Update `01 - Roadmap.md`, `00 - Start Here.md`, `99 - Glossary.md`, and append an entry to `98 - Vault Operations/Agent Prompts/_Enhancement Progress.md`.
- Re-verify version-sensitive claims at that time (the Verification Log dates tell it what's aging).

Keeping Phase A (study/synthesize) and Phase B (write into the vault) apart is deliberate: it means the expensive reading happens once and is auditable before a single vault note changes.
