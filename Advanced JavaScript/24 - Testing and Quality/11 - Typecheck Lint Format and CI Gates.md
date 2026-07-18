---
tags: [testing, ci, linting, tooling]
module: "24 - Testing and Quality"
priority: important
status: not-started
aliases: [CI pipeline, quality gates, ESLint]
verified_on: 2026-07-12
version_scope: "ESLint 9 flat config, TypeScript 5.x"
---

# Typecheck, Lint, Format and CI Gates

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: explain what each gate uniquely catches, why formatting is not linting, and how to order a pipeline for fast feedback.
- Production signal: main is always releasable; broken code is caught in minutes, pre-merge, by the cheapest applicable gate.
- Dependencies: [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]], [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|tsconfig]]

## Source Anchors

- [TypeScript: tsc CLI](https://www.typescriptlang.org/docs/handbook/compiler-options.html)
- [ESLint: documentation](https://eslint.org/docs/latest/)
- [typescript-eslint: type-aware linting](https://typescript-eslint.io/getting-started/typed-linting/)
- [Prettier: Why Prettier](https://prettier.io/docs/why-prettier)
- [GitHub Actions: documentation](https://docs.github.com/en/actions)

## 1. Concept — Four Gates, Four Distinct Failure Classes

The quality pipeline is [[24 - Testing and Quality/01 - Testing Mental Model|the mental model]]'s "static layer," industrialized. Each tool detects something the others structurally cannot:

- **Typecheck (`tsc --noEmit`)** — value/shape contradictions across the whole program: nulls unhandled, wrong arguments, impossible states ([[23 - TypeScript Deep Dive/01 - Type System Mental Model|types]]). Note: in bundler setups (Next, Vite), the dev server *transpiles without checking* — type errors don't stop `next dev`. If CI doesn't run `tsc`, nothing does.
- **Lint (ESLint)** — legal-but-suspicious *patterns*: unawaited promises (`@typescript-eslint/no-floating-promises` — the async bug from [[08 - Async JavaScript/05 - Async Error Handling|module 08]] as a build error), missing hook deps (`react-hooks/exhaustive-deps` — [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|stale closures]] caught mechanically), unused vars, `==` vs `===`. Type-aware rules (typescript-eslint with project info) are the high-value tier.
- **Format (Prettier)** — no bugs at all; it eliminates a *category of discussion*. Style stops consuming review attention and diffs stop containing noise. Formatting is not linting: one prints a canonical layout, the other judges semantics-adjacent patterns. Let Prettier own layout, disable ESLint's stylistic rules (`eslint-config-prettier`), end the turf war.
- **Tests + build** — behavior (this module) and "does it actually compile/bundle for production" (a failing `next build` on a type-legal, lint-clean repo is real and common — e.g., a client component importing server-only code — [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|boundaries]]).

Ordering follows cost: cheap-and-fast fails first (format check seconds, lint+typecheck tens of seconds, unit/component tests ~a minute, build minutes, E2E last — often parallelized in CI but with the same *feedback* priority). Locally, a pre-commit hook running format + lint on staged files keeps the loop instant; CI re-runs everything because local hooks are skippable (`--no-verify`) and machines differ.

## 2. Why It Matters

- Every gate is a class of production incident converted into a red X on a PR: the unawaited promise that swallowed a checkout error, the missing dep that shipped a stale closure, the `next build` failure discovered at deploy time on Friday.
- Interview probes ("what does your CI look like?", "lint vs typecheck?") test whether you understand *what each tool can know* — the same detector-thinking as the testing layers.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a team's CI is `npm test` only. Three incidents in one quarter:

1. A refactor renamed a prop; one usage was missed. Tests didn't cover that screen. Runtime: `undefined` rendered into the UI. — *Would have been a `tsc` error in 40 seconds.*
2. `saveDraft()` (async) called without `await` in an event handler; its failure vanished ([[08 - Async JavaScript/04 - Promise Rejections|unhandled rejection]]); users lost drafts silently. — *`no-floating-promises` flags exactly this.*
3. A PR "worked in dev" but `next build` failed at deploy: a server-only import inside a client component. — *A build gate catches it pre-merge.*

Fix — the boring, correct pipeline:

```yaml
# .github/workflows/ci.yml (essentials)
jobs:
  quality:
    steps:
      - run: npm ci
      - run: npx prettier --check .        # seconds — canonical layout
      - run: npx eslint .                  # pattern bugs, incl. type-aware + hooks rules
      - run: npx tsc --noEmit              # whole-program contradiction check
      - run: npx vitest run                # unit + component behavior
      - run: npm run build                 # production compile: the deploy can't fail a way CI didn't try
  e2e:
    needs: quality                         # don't spend minutes if seconds already failed
    steps: [ ... playwright test ... ]
```

Tradeoffs: pipeline time is a real cost — mitigate with caching, running independent gates in parallel, and E2E gated behind the cheap stages. Strictness has an adoption cost on legacy code (adopt incrementally — [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|strict migration]]); rules the team genuinely disagrees with breed `eslint-disable` sprawl — curate the rule set, don't maximize it. And a green pipeline is necessary, not sufficient: it's the floor that lets human review focus on design and correctness instead of style and typos.

> [!tip] The gate belongs where the knowledge lives
> Choosing between "add a lint rule," "add a type," or "add a test" for a recurring bug class: if it's expressible as a shape, make it a type (whole-program, zero runtime cost); if it's a syntactic pattern, a lint rule (instant, no cases to enumerate); only if it's genuinely behavioral does it need a test. Cheapest detector that can know the fact — same principle, static edition.

## 4. Interview Answer

Short answer:

> Four gates, four failure classes: Prettier makes layout a non-topic; ESLint catches legal-but-wrong patterns — floating promises, missing hook deps; `tsc --noEmit` catches whole-program shape contradictions (and must run explicitly, since bundler dev servers transpile without checking); tests catch behavior; the production build catches what only bundling reveals. CI orders them cheapest-first for fast feedback, and E2E runs after the cheap gates pass.

Deeper answer:

> The design principle is pushing each bug class to the cheapest gate that can know about it — a recurring bug becomes a type if it's a shape, a lint rule if it's a pattern, a test only if it's behavior. Local pre-commit hooks give instant feedback but are skippable, so CI is the enforcement point. The failure modes I watch for: teams that run tests but never `tsc` (type errors ship because dev mode doesn't check), stylistic ESLint rules fighting Prettier (use eslint-config-prettier), disable-comment sprawl (signals the rule set needs curation, not more suppression), and pipelines so slow people batch changes — undermining the small-PR feedback loop the pipeline exists to serve.

## 5. Practice

1. <details><summary>Why does `next dev` happily run code that `tsc --noEmit` rejects, and what's the operational consequence?</summary>Dev servers use fast transpilers (SWC/esbuild) that strip types without checking them — type errors become invisible until something runs `tsc`. Consequence: without an explicit typecheck gate in CI, type errors accumulate and surface either in `next build` (which does typecheck by default, at deploy-adjacent time) or at runtime. The fix is a dedicated `tsc --noEmit` CI step — fast, and it fails minutes after the mistake, not at deploy.</details>

2. <details><summary>Which specific lint rules pay the highest frontend rent, and what taught bug does each map to?</summary>`@typescript-eslint/no-floating-promises` → unawaited async, swallowed rejections ([[08 - Async JavaScript/05 - Async Error Handling|async errors]]). `react-hooks/exhaustive-deps` → stale closures in effects ([[14 - JavaScript in React and Next.js/03 - Stale Closures|module 14]]). `no-await-in-loop` (advisory) → accidental request waterfalls ([[22 - Next.js Deep Dive/06 - Data Fetching Patterns|waterfalls]]). `@typescript-eslint/no-misused-promises` → async handlers where a void return is expected (form onSubmit). Each converts a production incident class from this vault into editor-time feedback.</details>

3. <details><summary>Your team's pipeline takes 25 minutes and people have started merging with `--no-verify` + admin override. Diagnose and fix.</summary>The pipeline's cost has exceeded its perceived value, so it's being routed around — the worst state (all cost, no protection). Fix: parallelize independent gates, cache dependencies/build artifacts, run E2E selectively (critical paths on PR, full nightly), shard tests, and measure which stage dominates. Also address the culture: overrides must be exceptional and visible. A gate only works if passing it is easier than bypassing it.</details>

4. <details><summary>Format-on-save already runs Prettier locally. Why still `prettier --check` in CI?</summary>Local setups drift: a teammate's editor lacks the extension, a file was edited in a terminal, a generated file slipped in unformatted. CI is the only environment every change actually passes through, so it's where the invariant "main is canonically formatted" is enforced. Seconds of cost buy zero-noise diffs forever. Same logic as re-running lint/typecheck in CI despite pre-commit hooks: hooks are conveniences, CI is the contract.</details>

## Related Notes

- [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]]
- [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|Modules, tsconfig and Package Types]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
