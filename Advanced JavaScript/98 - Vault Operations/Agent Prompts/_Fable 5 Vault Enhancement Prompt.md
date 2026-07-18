# Fable 5 — Vault Enhancement Prompt

Copy everything below the line into a new session with this vault folder connected.

---

You have access to my Obsidian vault "Advanced JavaScript" (140 notes, folders 02–18 plus Start Here, Roadmap, Glossary). It is a training system for becoming a mature mid-level/senior frontend developer who understands JavaScript, React, and Next.js behind the scenes — not memorized definitions, but mechanisms, production bugs, tradeoffs, and interview answers.

Your job: extend and upgrade the vault. Work in the phases below, in order. Before writing anything, read `00 - Start Here.md`, `01 - Roadmap.md`, and 3–4 existing concept notes (e.g. `03 - Scope and Variables/05 - Closures.md`, `14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js.md`) to internalize the house style.

## Non-negotiable conventions (match existing notes exactly)

1. Every concept note uses the existing pattern: **Maturity Target** (priority, study time, interview signal, production signal, dependencies) → **Source Anchors** (real links: tc39.es/ecma262, MDN, HTML Living Standard, react.dev, nextjs.org/docs, web.dev) → numbered sections covering: concept, why it matters, accurate mechanism, mental model, real frontend example, common bugs/edge cases, interview answer, practice questions with `<details><summary>Show answer</summary>` blocks.
2. Wikilinks use full path + alias form: `[[03 - Scope and Variables/05 - Closures|Closures]]`. Every new note links to its prerequisites and gets linked from related existing notes.
3. Filenames: `NN - Title.md`, no special characters. Each folder ends with a `Checklist` note.
4. Code examples must be realistic frontend code (React/Next/fetch/DOM), traced step by step, with the buggy version AND the production-safe fix plus its tradeoff.
5. Never dumb content down; target: could a strong senior say this in a system-design or deep-dive interview without embarrassment. Verify claims against the linked sources — if unsure about current React 19 / Next.js 15+ behavior, search the official docs first.
6. Do NOT renumber or rename existing folders/files (it breaks links). New modules get new numbers (19+). Update `01 - Roadmap.md` to slot them into the correct *logical* study order regardless of folder number.

## Phase 1 — Obsidian infrastructure upgrade

1. **Frontmatter overhaul** on all notes. Replace the current identical frontmatter with real, per-note metadata:
   ```yaml
   ---
   tags: [javascript, closures, scope]      # real per-note topic tags; add react/nextjs/dom/security where relevant
   module: "03 - Scope and Variables"
   priority: must-know                       # must-know | important | deep-dive (move the inline #must-know tags here)
   status: not-started                       # not-started | learning | solid — this is MY progress tracker, so reset all to not-started
   aliases: [TDZ]                            # only where a common short name exists (TDZ, IIFE, HOF, GC, RSC…)
   ---
   ```
2. **Folder MOCs**: create `00 - <Module Name> MOC.md` inside every numbered folder: 2–3 sentence module summary, prerequisite modules, recommended reading order with wikilinks, and a "you're done when" list pulled from the module checklist.
3. **Callouts**: convert buried traps/warnings/key insights in existing notes into Obsidian callouts — `> [!warning]` for footguns, `> [!tip]` for production patterns, `> [!example]` for traced walkthroughs, `> [!question]` for self-tests. Don't over-apply; 2–5 per note.
4. **Home dashboard**: create `_Dashboard.md` at root with Dataview queries (notes by status, by priority, by module) inside code blocks, plus a plain-markdown fallback list in case Dataview isn't installed. Recommend the plugins in a comment: Dataview, Spaced Repetition, and note that the dependency map could become a Canvas.
5. Add a Mermaid diagram of the module dependency graph to `01 - Roadmap.md`.

## Phase 2 — New modules (the big content gaps)

Create these folders with the full house-style note pattern:

**`19 - DOM and Browser APIs`** (must-know; logically belongs after Event Loop)
01 DOM Fundamentals and the Render Pipeline (DOM/CSSOM, reflow vs repaint, layout thrashing) · 02 Event Propagation (capturing, target, bubbling, `stopPropagation` vs `stopImmediatePropagation`, `preventDefault`, passive listeners) · 03 Event Delegation (why lists/tables use it, `closest()`, React synthetic event connection) · 04 Custom Events and EventTarget · 05 Browser Storage (cookies vs localStorage vs sessionStorage vs IndexedDB — size, sync/async, security, when each is wrong) · 06 Observers (IntersectionObserver for lazy loading/infinite scroll, ResizeObserver, MutationObserver) · 07 fetch Deep Dive (Request/Response, headers, body streams, credentials modes, timeouts, retries) · 08 Forms and FormData · 09 Web Workers and Offloading Work (structured clone, transferables, when a worker is the right fix vs chunking) · 10 Service Workers and PWA Basics · 11 History and Navigation APIs (SPA routing mechanics — what Next's router sits on) · 12 Checklist

**`20 - Network and Security`** (must-know for senior signal)
01 HTTP Essentials for Frontend (methods, status codes, headers, HTTP/1.1 vs 2 vs 3 at overview level) · 02 HTTP Caching (Cache-Control, ETag, revalidation — connect to the Next.js cache) · 03 CORS Correctly Explained (same-origin policy, preflight, common myths — e.g. CORS protects the user, not the server) · 04 Cookies and Auth Patterns (session vs JWT, httpOnly/SameSite/Secure, where tokens should live and why localStorage is risky) · 05 XSS (reflected/stored/DOM-based, why React escapes by default, `dangerouslySetInnerHTML`, sanitization) · 06 CSRF and CSP · 07 Prototype Pollution and Supply-Chain Basics · 08 WebSockets, SSE, and Polling (choosing a realtime strategy) · 09 Checklist

**`21 - React Internals and Patterns`** (must-know; complements folder 14 — don't duplicate it, link to it)
01 Render and Commit Phases (what a "render" actually is; why render functions must be pure) · 02 Reconciliation and Keys (diffing rules, why index keys corrupt state, element type identity) · 03 Fiber and Scheduling Overview (interruptible rendering, lanes — overview depth, not internals trivia) · 04 State Batching and Updater Queues (React 18 automatic batching, functional updates) · 05 Context: Mechanics and Performance (propagation, why consumers re-render, splitting contexts) · 06 Refs Beyond DOM (`useRef` as instance variable, callback refs, `forwardRef`) · 07 useLayoutEffect, useInsertionEffect and Effect Timing (full timeline: render → mutation → layout effects → paint → passive effects) · 08 useSyncExternalStore (tearing, subscribing to external stores — how Zustand/Redux bind in) · 09 Suspense and Concurrent Features (transitions, `useDeferredValue`, streaming SSR relationship) · 10 React 19 (actions, `useActionState`, `useOptimistic`, `use()`, form actions, React Compiler and what it means for manual memoization) · 11 Custom Hook Design Patterns · 12 Controlled vs Uncontrolled Components · 13 Checklist

**`22 - Next.js Deep Dive`** (must-know; extends the two notes in folder 14 — link, don't duplicate)
01 Rendering Strategies (SSR, SSG, ISR, streaming, PPR — decision framework) · 02 The Caching Layers (Request Memoization, Data Cache, Full Route Cache, Router Cache — the #1 source of "why is my data stale" bugs) · 03 Revalidation (`revalidateTag`, `revalidatePath`, time-based, on-demand) · 04 Server Actions (mechanics, serialization boundary, security model, progressive enhancement) · 05 Route Handlers and Middleware (edge vs Node runtime constraints) · 06 Data Fetching Patterns (parallel vs sequential, `Promise.all` in RSC, waterfalls) · 07 Metadata, SEO and the head · 08 Asset Optimization (next/image, next/font — what they actually do) · 09 Checklist

## Phase 3 — Fill gaps inside existing folders (append with next numbers; renumber only the checklist note if needed, updating links)

- `09 - Event Loop Advanced`: add **Node.js Event Loop vs Browser** (libuv phases at overview level, `setImmediate`, `process.nextTick`, why this matters for SSR code paths).
- `12 - Advanced Language Concepts`: add **Numbers and Floating Point** (IEEE 754, `0.1 + 0.2`, `Number.EPSILON`, safe integers, parsing pitfalls, money-handling patterns); **Strings, Unicode and Template Literals** (UTF-16 code units vs code points, `length` lies, emoji/grapheme traps, tagged templates, `normalize`); **Proxy and Reflect** (traps, how Vue/MobX/Immer-adjacent reactivity works, invariants, performance cost); **Typed Arrays and Binary Data** (ArrayBuffer, DataView, Blob, File, base64 — file upload/download scenarios); **Intl** (NumberFormat, DateTimeFormat, RelativeTimeFormat, Collator — kill hand-rolled formatting).
- `10 - Modules`: add **From Source to Browser** (transpilers Babel/SWC, polyfills vs syntax transforms, browserslist, source maps, what "supports ES2020" actually means, brief bundler comparison).
- `13 - Performance and Memory`: add **Core Web Vitals and Measuring** (LCP, INP, CLS, long tasks, `PerformanceObserver`, connecting back to event-loop and rendering notes).
- `06 - Objects and Prototypes`: verify getters/setters and `structuredClone` are covered properly in existing notes; extend rather than add if thin.

## Phase 4 — Integration pass

1. Update `01 - Roadmap.md`: insert modules 19–22 and the new notes into the phase table at their correct logical positions (19 after Event Loop; 20 after Error Handling; 21 and 22 around folder 14), update the dependency map and priority labels.
2. Update `00 - Start Here.md`: folder structure listing, fast-track list (add event delegation, Next caching layers, reconciliation/keys).
3. Update `99 - Glossary.md` with new terms (reflow, preflight, hydration mismatch already there? verify; add RSC payload, lane, tearing, ETag, CSP, transferable…).
4. Update `18 - Revision Plans`: extend the complete checklist and the 30-interview-questions / output-questions sets with items from the new modules (e.g. event-delegation question, CORS question, keys question, Next caching question).
5. Add cross-links both directions: e.g. `09/06 Rendering and UI Responsiveness` ↔ `19/01 DOM Fundamentals`; `08/06 AbortController` ↔ `19/07 fetch Deep Dive`; `14/09 Server vs Client` ↔ `22/02 Caching Layers`.

## Phase 5 — Verification (do not skip)

- Run a link check: grep all `[[...]]` targets and confirm every one resolves to a real file.
- Confirm every new note has: valid frontmatter, Maturity Target, ≥3 working Source Anchor URLs, at least one traced code example, at least one bug→fix→tradeoff, at least 3 practice Q&As in `<details>` blocks.
- Confirm no existing note lost content during frontmatter/callout edits.
- Print a final summary: files created, files modified, link-check result.

Work module by module and report progress after each phase. Quality over speed — one excellent note beats three shallow ones. If context/session limits force a stop, finish the current module cleanly and tell me the exact resume point.
