---
tags:
  - javascript
  - runtime
  - ecmascript-vs-javascript
module: 02 - JavaScript Runtime Foundations
priority: must-know
status: solid
verified_on: 2026-07-23
version_scope: TC39 process (stage 2.7 added late 2023); Node global fetch (v18+); WinterTC / Ecma TC55; Next.js 16 proxy.ts (renamed from middleware.ts)
---

# ECMAScript vs JavaScript

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Outcome: separate language rules from host/runtime behavior before explaining or debugging.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)
- [HTML Living Standard: event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [TC39 process document](https://tc39.es/process-document/)
- [WinterTC: Minimum Common Web API](https://min-common-api.proposal.wintertc.org/)

## 1. Simple Explanation

ECMAScript is the official language specification. JavaScript is what developers use in real environments: an ECMAScript engine plus host APIs such as the DOM, timers, fetch, storage, files, networking, and rendering.

Blueprint vs building is a good first analogy, but the mature version is sharper: ECMAScript defines what the language means; the host defines what the environment can do.

## 2. Why It Matters

Many frontend explanations become weak because they mix layers:

- "Promises are JavaScript, so the browser event loop is JavaScript."
- "`setTimeout` is a JavaScript feature."
- "`window` should exist because this file is JavaScript."
- "Next.js can run this code anywhere because it is JavaScript."

Those statements hide the real boundary. A browser, Node.js, an edge runtime, and a React Native runtime can all execute ECMAScript, but they do not expose the same host APIs or scheduling rules.

## 3. Accurate Mechanism

ECMAScript defines:

- Syntax and grammar.
- Language types: Undefined, Null, Boolean, String, Symbol, Number, BigInt, and Object.
- Built-in objects such as `Array`, `Object`, `Map`, `Set`, `Promise`, `Date`, and `RegExp`.
- Evaluation algorithms and abstract operations such as `ToNumber`, `GetValue`, and `SameValue`.
- Execution contexts, lexical environments, realms, agents, modules, and jobs.
- Promise behavior at the language level.

ECMAScript does not define:

- `window`, `document`, the DOM, layout, or paint.
- `fetch`, `localStorage`, IndexedDB, or browser navigation.
- `setTimeout`, UI events, rendering opportunities, or the browser event loop.
- Node.js APIs such as `fs`, `process`, `Buffer`, or streams.
- React rendering, Next.js routing, bundling, transpilation, or hydration.

Those are provided by host environments, platform specifications, frameworks, or tooling.

### globalThis (ES2020)
`globalThis` is a standardized ECMAScript property that provides a unified way to access the global object across any runtime environment.
* In browser runtimes, it points to `window` (or `self` in Web Workers).
* In Node.js runtimes, it points to `global`.
* In edge worker runtimes, it points to the global scope of the worker.

> [!tip] globalThis for isomorphic code
> This enables isomorphic (server-and-client) JavaScript execution in Next.js without throwing environment-specific `ReferenceErrors` (e.g. `ReferenceError: window is not defined` during SSR).

## 4. Layer Attribution Model

The question this model answers is *"which layer owns this behavior?"* — not *"what is the runtime made of."* Those are different questions, and conflating them is itself a layer error.

**The runtime proper is two layers.** ECMAScript is not a peer layer in it — it is the *contract* the engine implements. Framework and application code sit *on top of* the runtime; they consume it, they are not part of it.

### Inside the runtime

| Layer                          | Owns                                                                                                                                                                 | Example question                                   |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Engine (implements ECMAScript) | Language semantics, execution contexts, the agent, the job/microtask queue machinery, GC, JIT optimization                                                           | Why does `let` throw before initialization?        |
| Host environment               | Everything ECMA-262 leaves abstract (`HostEnqueuePromiseJob`, `HostCallJobCallback`), task sources, the event loop, external APIs (`setTimeout`, DOM, `fetch`, `fs`) | Why does `setTimeout` run after promise callbacks? |

The event loop is **host-owned**, not engine-owned: it is specified in the HTML Living Standard for browsers and implemented by libuv in Node.js. ECMA-262 defines only the *job* abstraction and hands scheduling to the host. See [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]].

### Above the runtime

| Layer             | Owns                                                                              | Example question                                      |
| ----------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Framework/tooling | Selects which host you run on; transforms language semantics; rendering, bundling | Why does this code fail during Next.js server render? |
| Application       | State, ownership, user flow                                                       | Which request is still relevant to the current UI?    |

> [!warning] Tooling is not cleanly "above" the runtime
> The clean stack is a teaching simplification. Tooling can change which runtime you are on and can change observable language semantics — so "it's just my build config" is often the wrong first hypothesis for a behavior bug.
>
> - **Downleveling changes async ordering.** Babel/SWC compiling `async/await` to generators plus a promise polyfill produces different microtask interleaving than native `await`. Code that relies on exact tick ordering can pass natively and fail transpiled.
> - **The framework picks the host.** Next.js does not merely render — it decides whether your module evaluates in Node.js or in the Edge runtime (workerd), which has a different global set and no `fs`. Same source file, different host layer.
> - **Bundler resolution decides module semantics.** Whether a dependency resolves to ESM or CJS determines live bindings vs. a snapshotted copy of the exports — a language-level difference, chosen by a resolver.
>
> Better mental model: tooling is a **runtime selector and semantics transformer**, not a stratum of the runtime.

This model is useful in interviews because it shows you can reason from the correct source of truth — and naming the boundary between "inside the runtime" and "on top of it" is exactly the distinction weaker candidates blur.

## 5. Support, Transpilation, and Polyfills

Do not collapse "the spec defines it" into "every runtime supports it."

| Question                                            | Correct layer                     |
| --------------------------------------------------- | --------------------------------- |
| What does optional chaining mean?                   | ECMAScript language semantics.    |
| Does this browser parse optional chaining natively? | Engine support.                   |
| Can Babel/TypeScript transform the syntax?          | Tooling/transpilation.            |
| Does the runtime have `Array.prototype.at`?         | Built-in API support or polyfill. |
| Does `fetch` exist in this environment?             | Host/runtime API support.         |

> [!tip] Know what can be polyfilled
> Transpilers can rewrite syntax. Polyfills add missing runtime APIs when practical. Some behavior cannot be safely polyfilled everywhere, especially host capabilities such as layout, storage, workers, or process APIs.

```ts
// Syntax feature: can often be transpiled.
const label = user?.profile?.name ?? "Anonymous";

// Built-in method: older targets may need a polyfill or fallback.
const last = items.at ? items.at(-1) : items[items.length - 1];

// Host API: must exist in the runtime or be replaced by a runtime-specific API.
const response = await fetch("/api/users");
```

> [!tip] Check the support layer first
> Production rule: before using a feature, know whether you need syntax transformation, a polyfill, feature detection, or a different runtime boundary.

### How Features Become ECMAScript: The TC39 Process

New language features move through TC39's staged process before landing in the annual ECMAScript edition:

| Stage | Meaning                                                                             |
| ----- | ----------------------------------------------------------------------------------- |
| 0     | Strawperson — an idea.                                                              |
| 1     | Proposal — problem accepted as worth solving.                                       |
| 2     | Draft — initial spec text exists.                                                   |
| 2.7   | Approved for implementation and testing (added to the process in 2023).             |
| 3     | Candidate — tests written; awaiting native implementations and real-world feedback. |
| 4     | Finished — two+ implementations, tests pass; merged into the next annual edition.   |

> [!warning] Stage 3 is not "safe to rely on"
> Stage 3 proposals have been changed or demoted after real-world feedback (`Array.prototype.group` was renamed — eventually to the static `Object.groupBy`/`Map.groupBy` — because the prototype method broke websites; ShadowRealm was demoted from stage 3 back to stage 2 in September 2023 over unresolved web-platform integration, and has since only climbed back to 2.7). Only stage 4 is finished. In production, "the proposal exists" and "my target runtimes ship it" are separate questions.

### Server Runtimes Converge: WinterTC

"Host API" no longer means "browser-only" — it means "defined outside ECMA-262." `fetch` is specified by WHATWG, yet it ships in Node.js 18+, Deno, Bun, and edge runtimes. **WinterTC** (Ecma TC55, formerly the WinterCG community group) standardizes a *Minimum Common Web API* — a subset of web platform APIs (`fetch`, `URL`, streams, `TextEncoder`, timers, `crypto`, and more) that server-side runtimes implement for interoperability. This is why the same data-fetching code can run in a browser, a Node server, and an edge function, while `fs` or `document` still cannot.

## 6. Real Frontend Example

```tsx
// This component mixes three layers:
// 1. ECMAScript: async/await, Promise, optional chaining, nullish coalescing.
// 2. Browser host APIs: fetch and AbortController.
// 3. React: useEffect cleanup and state updates.
function UserCard({ userId }: { userId: string }) {
  const [user, setUser] = React.useState<User | null>(null);

  React.useEffect(() => {
    const controller = new AbortController();

    async function load() {
      const response = await fetch(`/api/users/${userId}`, {
        signal: controller.signal
      });

      const data = await response.json();

      // Optional chaining and nullish coalescing are ECMAScript language features.
      setUser({ ...data, displayName: data.profile?.name ?? 'Anonymous' });
    }

    load().catch(error => {
      // AbortController is a browser API; AbortError is expected when cleanup runs.
      if (error.name !== 'AbortError') throw error;
    });

    // React owns when cleanup runs; the browser owns what abort means for fetch.
    return () => controller.abort();
  }, [userId]);

  return <Profile user={user} />;
}
```

## 7. Common Production Bug

> [!warning] window is missing during SSR
> Bug: code reads `window.localStorage` at module top level in a Next.js file.

```ts
// Problem: this can run during server rendering where window does not exist.
const theme = window.localStorage.getItem('theme');
```

Fix the layer mismatch:

```tsx
'use client';

function ThemeReader() {
  const [theme, setTheme] = React.useState('light');

  React.useEffect(() => {
    // Browser-only API is read after the component is running on the client.
    const stored = window.localStorage.getItem('theme');
    if (stored) setTheme(stored);
  }, []);

  return <ThemePreview theme={theme} />;
}
```

## Real-World Use Cases

### Sharing validation code across browser, server, and edge middleware

Next.js's proxy layer (`proxy.ts`, renamed from `middleware.ts` in Next.js 16) runs on an edge runtime that exposes roughly the WinterTC Minimum Common Web API — no Node APIs, no DOM. A shared URL-building helper survives all three environments only if it sticks to ECMAScript plus common Web APIs.

```ts
// lib/build-search-url.ts — imported by proxy.ts, a Server Component, and a Client Component
export function buildSearchUrl(base: string, filters: Record<string, string>) {
  const url = new URL(base);                          // URL: common Web API
  for (const [key, value] of Object.entries(filters)) // Object.entries, for..of: ECMAScript
    url.searchParams.set(key, value);                 // URLSearchParams: common Web API
  return url.toString();
}

// This one line would break the edge build — fs is a Node host API:
// import { readFileSync } from "fs";
```

What runs where is decided by the host layer, not the language: the syntax is portable everywhere, the APIs are not. See [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]].

### Analytics utility crashing inside a Web Worker

You move product-search indexing into a Web Worker for responsiveness, and a shared telemetry util imported by the index code throws `ReferenceError: window is not defined`. Workers run the same ECMAScript but a different host global scope.

```ts
// utils/telemetry.ts — before
// Crashes in a worker: window is a main-thread browser global, not a language feature.
const page = window.location.pathname;
```

```ts
// utils/telemetry.ts — after
// Worker-safe: globalThis is ECMAScript (ES2020) and exists in every runtime;
// guard the host-specific part explicitly.
const page =
  typeof globalThis.location !== "undefined" ? globalThis.location.pathname : "worker";
```

Fails because `window` belongs to one specific host scope, while `globalThis` is defined by the language for all of them — the exact boundary this note draws.

### CI breaks on "works on my machine": global fetch and Node versions

A shared API client uses global `fetch`. It works locally on Node 20 but the CI image runs Node 16, and every test dies with `ReferenceError: fetch is not defined`. Nothing about the *language* changed between those Node versions.

```ts
// api-client.ts — fine in browsers, Node 18+, Deno, Bun, edge runtimes
export async function getOrders(): Promise<Order[]> {
  const response = await fetch(`${API_BASE}/orders`);
  if (!response.ok) throw new Error(`Orders request failed: ${response.status}`);
  return response.json();
}
```

`fetch` is a WHATWG host API that Node only started shipping in v18 — a runtime API support question, not an ECMAScript version question, so the fix is bumping the runtime (or injecting `undici`), not transpiling.

> [!tip] Diagnose by layer
> When a "JavaScript feature" is missing, ask in order: syntax (transpile), built-in (polyfill), host API (runtime version or feature detection). Naming the layer usually names the fix. See [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]].

## 8. Interview Answer

**Short version:** ECMAScript is the language specification. JavaScript in practice is ECMAScript implemented by an engine and embedded in a host such as a browser, Node.js, or an edge runtime.

**Deeper version:** ECMAScript defines the core language: syntax, types, objects, functions, modules, promises, jobs, execution contexts, and abstract operations. Browser APIs such as DOM, fetch, timers, storage, events, and rendering are host behavior, mostly defined outside ECMA-262. That distinction matters because the same language code can behave differently depending on whether it runs in a browser, Node.js, a worker, an edge runtime, or a framework server/client boundary.

## 9. Common Mistakes

- Saying `fetch`, `setTimeout`, or `window` are ECMAScript features.
- Saying "JavaScript is single-threaded" without mentioning workers, agents, host APIs, or async I/O.
- Assuming TypeScript runtime behavior exists after compilation. TypeScript types are erased unless runtime validation is added.
- Confusing transpilation support with native engine support.
- Treating a TC39 proposal as stable before it reaches the finished stage and ships in target engines.
- Assuming browser and server JavaScript share the same globals because the syntax is the same.
- Counting frameworks and application code as layers *of* the runtime. They run on top of it — the runtime is engine + host.
- Saying the engine owns the event loop. The engine owns the job queue machinery; the host owns the loop that drains it.
- Assuming transpiled `async/await` preserves native microtask ordering.

## 10. Practice

1. Explain the difference between ECMAScript, a JavaScript engine, and a JavaScript runtime.
2. Put these into the right layer: `Promise`, `fetch`, `document`, `Map`, `setTimeout`, `process`, `useEffect`, `import`.
3. Why can `Promise` exist in both browser and Node.js, while `window` does not?
4. What breaks when a Client Component accidentally imports a module that reads `window` at top level?
5. Give a 30-second interview answer correcting this statement: "`setTimeout` is part of JavaScript."

<details>
<summary>Show answer</summary>
<ol>
<li>ECMAScript is the language specification. An engine implements that language. A runtime embeds the engine and adds environment APIs, scheduling, I/O, rendering, or framework boundaries.</li>
<li><code>Promise</code>, <code>Map</code>, and <code>import</code> are ECMAScript language/module features. <code>fetch</code>, <code>document</code>, and <code>setTimeout</code> are browser/host APIs, although some non-browser runtimes also provide compatible versions. <code>process</code> is Node.js runtime API. <code>useEffect</code> is React framework API.</li>
<li><code>Promise</code> is part of ECMAScript, so compliant engines expose it across browsers and Node.js. <code>window</code> is the browser global object, so Node.js and server runtimes do not expose it by default.</li>
<li>The import can evaluate on the server or in a non-browser build step. If the module reads <code>window</code> at top level, evaluation throws before React can defer it to an effect. The fix is to move the browser read into a Client Component/effect or isolate it behind a client-only boundary.</li>
<li>A good interview correction: "<code>setTimeout</code> is not part of ECMAScript itself. It is a host API provided by browsers and also by runtimes such as Node.js. ECMAScript defines promises and jobs; the host integrates timers, tasks, and event-loop behavior."</li>
</ol>
</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[99 - Glossary|Glossary]]
