# Review Prompt — System Design, Low Level Design, and Frontend System Design build

Copy everything below the line into a fresh session with the `Advanced JavaScript` vault folder (and its sibling `_Synthesis/` folder, if present) connected. This prompt is self-contained: assume you have **no prior context** about how this content was produced.

---

You are auditing a large recent addition to an Obsidian study vault called **Advanced JavaScript**. The vault belongs to a mid-level frontend developer (React/Next.js/TypeScript) preparing for senior interviews. Your job is to **review, not rewrite** — produce a rigorous findings report. Only edit files if I explicitly ask you to after seeing the report.

## What the vault is and its "mature bar"

Every concept note is meant to clear a "mature" bar: define the idea simply, name the *actual mechanism* (not a hand-wave), trace an example, name the real production/interview failure mode, then give a safe pattern with tradeoffs and short + deep interview answers. No beginner padding; no buzzwords left undefended.

## House conventions (verify the new content follows them)

- **Frontmatter** on every note: `tags`, `module`, `priority` (`must-know` | `important` | `deep-dive`), `status` (`not-started` | `learning` | `solid`), optional `aliases`. Version-sensitive notes (anything about React/Next/TS/tooling/tech versions or current facts) additionally carry `verified_on: YYYY-MM-DD` and `version_scope`.
- **Do not change any `status` value** — it's the learner's progress marker. Part of your audit is confirming the build did **not** reset any existing note's `status`.
- **Wikilinks** use full path + alias: `[[30 - Backend System Design/05 - Caching|Caching]]`. Every link must resolve to a real file.
- **Callouts**: `> [!warning]` for footguns, `> [!tip]` for production patterns.
- **8-part concept-note template**: frontmatter → `# Title` → `## Maturity Target` (priority, study time, interview signal, production signal, dependencies) → `## Source Anchors` (real URLs) → `## 1. Concept` → `## 2. Why It Matters` → `## 3. Real Frontend Example: Bug → Fix → Tradeoff` → `## 4. Interview Answer` (short + deeper) → `## 5. Practice` (`<details><summary>`…`</summary>`…`</details>`) → `## Related Notes`. Design **walkthrough** notes instead use a RADIO structure: Requirements → Architecture → Data Model → Interface → Optimizations → Interview Answer → Practice.
- New notes are appended after a module's existing files; **existing files are never renumbered**.

## What was added (the scope of your review)

**A. New module `30 - Backend System Design`** — MOC + 12 notes + checklist: delivery framework, networking/protocols, API design, data modeling, caching, sharding & consistent hashing, CAP & consistency, indexing & storage engines, numbers to know, the seven access patterns, deep-dive technologies, checklist. Each note has a "frontend mirror" tying the backend concept to its client-side equivalent.

**B. New module `31 - Low Level Design`** — MOC + 5 notes + checklist: delivery framework, design principles/SOLID, OOP concepts, design patterns, concurrency foundations, checklist. Examples are in TypeScript. The concurrency note argues JS's single-threaded event loop replaces mutexes with Web Workers + message passing.

**C. Expanded module `29 - Frontend System Design`** — grew from 5 notes to 21: 10 foundational concept notes (rendering strategies, data fetching at scale, component API design, frontend performance/Core Web Vitals, network & API design, state normalization & optimistic updates, i18n/RTL, offline & resilient UX, real-time UI patterns, accessibility in system design) and 6 RADIO walkthroughs (modal/dialog system, notification/toast system, data table, image carousel, chat/messaging app, e-commerce product page). The MOC reading order and checklist were rewritten; the framework note gained a "Real-World Use Cases" section.

**D. Integration edits to existing files** — backlinks were added into modules 17, 20, 21, 28, 29; and `00 - Start Here.md`, `99 - Glossary.md`, `01 - Roadmap.md`, `15 - Interview Preparation/00 - …MOC`, `18 - Revision Plans/01 - Complete… Checklist`, and `98 - Vault Operations/Agent Prompts/_Enhancement Progress.md` were updated. Confirm these edits are additive only (no content lost, no `status` changed).

**E. (If `_Synthesis/` is connected)** — 5 planning artifacts in the project root that fed the build; check that the vault notes match what those artifacts claim, and note that some source material was premium-locked and written at "framing depth" with in-note warnings.

## What to check — and how to weight it

1. **Factual accuracy, especially version-sensitive claims.** Independently re-verify these against primary/current sources (search the web; today's date matters):
   - Core Web Vitals thresholds and that **INP replaced FID** (which year?); the "good" values and the percentile they're measured at.
   - **Redis licensing history and the Valkey fork**; whether "Redis 8 / AGPLv3" and "BSD→SSPL 2024" are stated correctly.
   - **Kafka removing ZooKeeper (KRaft)** — which major version, what year.
   - The "2026 hardware / latency numbers" (intra-AZ, cross-AZ, cross-region latency; single-node RAM/SSD ceilings).
   - Any React/Next/TS specifics, and any claim carrying `verified_on`.
   Flag anything wrong, dated, or overstated, with the correct fact and a source.
2. **Mechanism correctness.** For each concept, is the named mechanism actually right (e.g., cache-aside vs write-through, cursor vs offset pagination, consistent hashing's "1/N keys move", optimistic-update reconciliation, virtual focus via `aria-activedescendant`, the APG pattern named for each widget)? Call out any hand-waving or subtly wrong explanation.
3. **House-style & template adherence.** Does every new note follow the 8-part template (or RADIO for walkthroughs), have real Source Anchor URLs, use callouts correctly, and carry proper frontmatter (including `verified_on`/`version_scope` where warranted)?
4. **Link integrity.** Grep every `[[…]]` wikilink in the new/edited files and confirm each resolves to a real file. Report any broken link.
5. **No regressions.** Confirm no existing note's `status` was changed and no existing content was removed by the integration edits.
6. **Redundancy / overlap.** Modules 20 (Network & Security), 22 (Next.js), 13 (Performance), 25 (Accessibility), 28 (Frameworks) already exist. Do the new module-29 foundational notes and the new modules 30/31 *cross-link* to those rather than duplicating them? Flag any note that re-teaches instead of referencing.
7. **Cross-domain wiring.** The build claims backend SD, LLD, and frontend concerns are "one idea at different scales" (e.g., in-process lock ↔ distributed lock ↔ client race guard; server cache ↔ client query cache; CAP eventual consistency ↔ optimistic UI). Are those bridges accurate, or are any of them forced/superficial?
8. **Pedagogical quality at the mature bar.** Are the Bug→Fix→Tradeoff examples realistic (not strawmen)? Do the practice Q&As force retrieval of the mechanism? Are the interview answers genuinely senior? Is anything padded or generic?
9. **Gaps.** Note important missing topics or weak spots — e.g., premium-locked areas that were written only at framing depth and still say `status: not-started`.

## Output format

Produce a structured report, no edits:

- **Summary verdict** (1 paragraph): overall quality and the highest-priority issues.
- **Findings table**: `file` · `issue` · `severity (blocker / major / minor / nit)` · `suggested fix` · `source URL if a fact`.
- **Version-sensitive fact-check**: each claim from item 1 marked confirmed / wrong / outdated, with the current fact and a source link.
- **Link-check result**: count checked, list any broken.
- **Redundancy & wiring assessment**: notes that duplicate existing modules; any forced cross-domain bridge.
- **Top 5 fixes** ranked by impact.

Be specific and cite file names and section headers. Where you claim a fact is wrong, provide the corrected fact and a source you actually fetched. Do not soften findings to be polite — this is a technical audit.
