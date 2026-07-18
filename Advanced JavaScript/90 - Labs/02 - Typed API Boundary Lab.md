---
tags: [labs, typescript, validation, api]
module: "90 - Labs"
priority: important
status: not-started
aliases: [typed boundary lab]
---

# Lab 02 — Typed API Boundary with Runtime Validation

Build one data-access layer that stands between an untrusted, misbehaving API and fully-typed UI code — schema-validated, error-modeled, cancellable, and tested against every way the API can lie.

## Prerequisites

- [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]] · [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Discriminated Unions]] · [[29 - Frontend System Design/09 - Network and API Design for Frontend|Network and API Design for Frontend]] · [[30 - Backend System Design/03 - API Design|API Design (why the wire looks like this)]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]] · [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|Async UI, Network Boundaries and MSW]]

## Build Brief

Vite + React + TypeScript (strict), Zod, Vitest, MSW. Product: a "team directory" page (list + detail) backed by a fake API *that you also write as MSW handlers* — including its hostile moods.

1. **The contract module**: Zod schemas for `Member` and the list envelope; all static types via `z.infer` — no hand-written duplicates.
2. **The boundary module**: `api.getMembers(signal)` / `api.getMember(id, signal)` returning a discriminated result: `{ kind: "ok", data } | { kind: "httpError", status, retriable } | { kind: "invalidData", issues } | { kind: "networkError" } | { kind: "aborted" }`. No exceptions escape; no `any` exists; `response.json()` lands in `unknown` and only exits through `.parse`/`.safeParse`.
3. **The UI**: list with loading/error/empty/data states driven by a `LoadState` union; detail view; retry buttons on retriable failures. UI code imports *types and the api module only* — it can't reach `fetch`.
4. **The hostile API**: MSW handler variants that return: valid data; a 500; a 200 with missing fields; a 200 with `snake_case` keys (contract drift); a 200 with `null` where a string was promised; a hung response (for cancellation); malformed JSON.

## Acceptance Criteria

- [ ] `tsc --noEmit` passes with `strict` + `noUncheckedIndexedAccess`; grep finds zero `as ` casts in src (except at most one documented `as const`) and zero `any`.
- [ ] Every hostile-API mood produces a *designed* UI state — never a blank screen, never an uncaught rejection in the console, never NaN/undefined rendered.
- [ ] Invalid-data failures log the Zod issues (observability) but show users a human message ([[11 - Error Handling/06 - API Error Handling Patterns|error patterns]]).
- [ ] Switching list → detail rapidly cannot render a stale member (abort on supersede — prove it with the hung-response handler).
- [ ] The schema is the single source of truth: deleting one field from the schema produces compile errors in every UI usage of that field.

## Debugging Tasks (create, observe, fix)

1. **The lying cast**: replace one `.parse` with `as Member` temporarily; run the missing-fields mood; document where the crash surfaces vs where the lie was told; restore the parse ([[23 - TypeScript Deep Dive/01 - Type System Mental Model|erasure]]).
2. **The silent drift**: change the API handler to `snake_case` without touching the client; watch the `invalidData` state catch it; then *disable* validation and document what the user would have seen instead.
3. **The double-fire**: remove the abort logic, click list→detail→back fast with the hung handler, and capture the stale render; restore and prove the fix ([[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|races]]).

## Testing Expectations

- MSW-based tests for every result-kind: each hostile mood asserts both the boundary's returned kind *and* the rendered UI state ([[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|MSW]]).
- A cancellation test proving the superseded request's data never renders ([[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|deterministic races]]).
- Unit tests on any response-mapping logic (DTO → view model) as pure functions.
- `onUnhandledRequest: "error"` — no request escapes the contract.

## Accessibility Expectations

- Loading/error/retry states are announced ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live regions]]); retry is a named button; the list is a real list; detail navigation manages focus ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|focus]]).

## Performance and Security Considerations

- Validation cost: measure `.parse` on a 1,000-member payload; decide (and document) whether per-item `safeParse` with partial acceptance beats all-or-nothing for this UX.
- Never render server-provided strings as HTML; note where XSS would enter if you did ([[20 - Network and Security/05 - XSS|XSS]]).
- Log validation failures without logging PII payloads wholesale.

## Interview Questions

1. "Our backend is TypeScript and we share types — why are you adding Zod?" Answer with the erasure/wire argument and the drift scenario you just built.
2. Why a discriminated result instead of thrown exceptions at this boundary? When would you choose exceptions?
3. Where exactly should the `AbortController` live and why — component, hook, or boundary module?
4. The 1,000-item payload made validation measurably slow. Options, and their failure-mode tradeoffs?

## Retrospective

[[98 - Vault Operations/Templates/Lab Retrospective Template|Template]] — plus: which hostile mood surprised you, and which production codebase you know needs this seam.

## Related Notes

- [[23 - TypeScript Deep Dive/00 - TypeScript Deep Dive MOC|TypeScript Deep Dive MOC]]
- [[24 - Testing and Quality/00 - Testing and Quality MOC|Testing and Quality MOC]]
- [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]]
- [[90 - Labs/00 - Labs MOC|Labs MOC]]
