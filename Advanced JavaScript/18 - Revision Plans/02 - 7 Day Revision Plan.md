---
tags: [javascript, revision, interview, 7-day-revision-plan]
module: "18 - Revision Plans"
priority: must-know
status: not-started
---

# 7 Day Revision Plan

This is the fast-track plan for interview preparation or a focused refresh. It assumes you already studied the vault and now need to turn recognition into confident recall, tracing skill, and production reasoning.

## Target Outcome

After 7 days, you should be able to:

- Explain the main JavaScript mechanisms without junior-level shortcuts.
- Solve mixed code-output questions by tracing the actual rule.
- Connect every language topic to a frontend bug, React behavior, Next.js boundary, performance issue, or API integration choice.
- Give concise interview answers under pressure.

## Daily Session Template

Use a 2-hour block when possible. If you only have 60 minutes, keep the recall, code trace, and bug explanation sections.

| Time | Activity | Output |
| --- | --- | --- |
| 15 min | Active recall | Write what you remember before opening notes. |
| 35 min | Deep review | Read the linked notes and correct your recall. |
| 25 min | Code tracing | Solve 2 to 4 output questions and explain each line. |
| 25 min | Production drill | Write one bug, one fix, one tradeoff, and one verification step. |
| 15 min | Interview answer | Say a 30-second answer and a deeper 2-minute answer. |
| 5 min | Weak-area log | Record what to revisit tomorrow. |

## Day 1: Runtime, Scope, and Hoisting

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can separate language rules from browser/runtime behavior.

Study:

- [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

Must produce:

- [ ] A one-page explanation of execution context creation vs execution.
- [ ] A code trace involving `var`, `let`, `const`, function declarations, and TDZ.
- [ ] A frontend bug explanation: a value is read before initialization during module or component setup.

Practice prompt:

```js
try {
  console.log(status);
} catch (error) {
  console.log(error.name); // ReferenceError: status is in the TDZ.
}

let status = "ready";
console.log(status); // "ready"
```

Interview answer target:

Hoisting means bindings are created during the environment setup phase. The important detail is how each binding is initialized: function declarations are usable early, `var` starts as `undefined`, and `let`/`const` exist but cannot be read before initialization because of the TDZ.

## Day 2: Closures, Functions, and `this`

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can explain call-site behavior and stale-state bugs without handwaving.

Study:

- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]

Must produce:

- [ ] A closure explanation that mentions bindings, not copied values.
- [ ] A `this` decision table: default, implicit, explicit, constructor, lexical.
- [ ] A bug/fix scenario where an extracted method loses its receiver.

Practice prompt:

```js
"use strict";

const user = {
  id: 42,
  readId() {
    return this.id;
  },
};

const read = user.readId;
console.log(user.readId()); // 42: called with user as receiver.

try {
  console.log(read()); // TypeError: this is undefined in strict mode.
} catch (error) {
  console.log(error.name);
}
```

Production drill:

Explain whether you would use `.bind`, an arrow wrapper, or a class field when passing a method as an event handler. Include the tradeoff in memory, readability, and prototype sharing.

## Day 3: Objects, Prototypes, Arrays, and Immutability

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can trace property lookup and prevent shared-reference bugs.

Study:

- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]

Must produce:

- [ ] A prototype-chain trace for an own property, inherited property, and missing property.
- [ ] A table of mutating vs non-mutating array methods.
- [ ] A React state update that copies every modified level.

Practice prompt:

```js
const state = [{ id: 1, profile: { name: "Mina" } }];
const next = [...state];

next[0].profile.name = "Sara";

console.log(state[0].profile.name); // "Sara": nested object is shared.
console.log(next[0] === state[0]); // true: only the outer array changed.
```

Production drill:

Rewrite the update so the changed item and changed nested object are new references, then explain how React uses identity to decide what changed.

## Day 4: Promises, Async/Await, Event Loop, and Rendering

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can order sync code, microtasks, tasks, and UI rendering opportunities.

Study:

- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]

Must produce:

- [ ] A code-output trace with sync logs, promises, `await`, and timers.
- [ ] A summary of `Promise.all`, `allSettled`, `race`, and `any`.
- [ ] A UI responsiveness plan for a long list transform.

Practice prompt:

```js
console.log("A");

setTimeout(() => console.log("B"), 0);

Promise.resolve().then(() => console.log("C"));

console.log("D");

// Output: A, D, C, B.
// Sync code runs first, promise reactions run as microtasks, timers run as tasks.
```

Production drill:

Explain how a long synchronous filter can delay typing feedback even if the data eventually renders correctly. Name one fix: memoization, splitting work, virtualization, a worker, or changing the UX.

## Day 5: Modules, Errors, API Integration, and Cancellation

Label: Important  
Estimated time: 2 hours  
Interview signal: You can design reliable data-loading behavior, not just call `fetch`.

Study:

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]

Must produce:

- [ ] A module explanation covering static imports, live bindings, evaluation, and circular import risk.
- [ ] An API error-handling flow for loading, validation, HTTP failure, abort, retry, and unexpected failure.
- [ ] A fetch example that aborts stale work.

Practice prompt:

```js
const controller = new AbortController();

async function loadUser(id) {
  const response = await fetch(`/api/users/${id}`, {
    signal: controller.signal,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

controller.abort(); // The fetch rejects with an AbortError if still in flight.
```

Production drill:

Explain why cancellation and "ignore stale result" are related but not identical. Cancellation stops work when supported; stale-result guards protect state even when work cannot be canceled.

## Day 6: Performance, Memory, and Advanced Concepts

Label: Important  
Estimated time: 2 hours  
Interview signal: You can reason from measurements and lifetime, not just use `useMemo` everywhere.

Study:

- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]

Must produce:

- [ ] A memory-leak checklist for listeners, timers, subscriptions, caches, and retained closures.
- [ ] A performance diagnosis that names the signal: CPU, memory, network, layout/rendering, or JS bundle size.
- [ ] A `Map`, `Set`, `WeakMap`, or object decision and why it fits the data lifetime.

Practice prompt:

```js
function attachResizeTracker(node) {
  const handler = () => {
    // This closure retains node while the listener exists.
    console.log(node.getBoundingClientRect().width);
  };

  window.addEventListener("resize", handler);

  return () => {
    window.removeEventListener("resize", handler);
  };
}
```

Production drill:

Explain how you would prove this listener is cleaned up after navigation. Mention repeated navigation, event listener counts, heap snapshots, or a small reproduction.

## Day 7: React, Next.js, Mock Interview, and Weak Areas

Label: Must-know  
Estimated time: 2 to 3 hours  
Interview signal: You can connect JavaScript mechanics to framework behavior without turning the answer into framework folklore.

Study:

- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]

Must produce:

- [ ] A stale-closure fix using functional state updates, dependencies, refs, or effect redesign.
- [ ] A dependency-array explanation based on reactive values.
- [ ] A Next.js server/client boundary explanation with a browser-API example.
- [ ] A 45-minute mock interview using [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]] and [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]].

Practice prompt:

```js
useEffect(() => {
  const controller = new AbortController();

  async function load() {
    const response = await fetch(`/api/search?q=${query}`, {
      signal: controller.signal,
    });
    const data = await response.json();
    setResults(data);
  }

  load().catch((error) => {
    if (error.name !== "AbortError") {
      setError(error);
    }
  });

  return () => {
    controller.abort(); // Prevents old requests from updating this screen later.
  };
}, [query]);
```

Production drill:

Explain why the dependency is `query`, why the controller is created inside the effect, and what still needs guarding if the API or environment does not support cancellation.

## Fast Tracks

Use these if time is limited.

| Situation | Path |
| --- | --- |
| Interview tomorrow | Day 4, Day 7, then [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]. |
| Weak at React bugs | Day 2, Day 5, Day 7, then [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]. |
| Weak at JS fundamentals | Day 1, Day 2, Day 3, then [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]. |
| Weak at async | Day 4, Day 5, then [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]. |
| Weak at production reasoning | Day 5, Day 6, Day 7, then [[17 - Practical Frontend Scenarios/01 - Fixing Stale Closure in React|Practical Scenarios]]. |

## Recovery Protocol

If you miss a day:

- Do not double the next day blindly.
- Keep the daily session template.
- Move the missed day to the weak-area log.
- Preserve Day 7 for integration and mock interview work.

If a concept is not clicking:

- Reduce it to one failing code example.
- Predict the output before running it.
- Write the exact mechanism in one sentence.
- Connect it to a real frontend bug.
- Revisit it 24 hours later.

## Done Means

The 7-day plan is done when:

- [ ] You completed at least one written output per day.
- [ ] You solved at least 15 code-output questions total.
- [ ] You explained at least 7 production bugs and fixes.
- [ ] You completed one mock interview.
- [ ] Your weak-area log has fixes, not just vague topic names.

## Sources

- ECMAScript Language Specification: https://tc39.es/ecma262/
- HTML Living Standard event loops: https://html.spec.whatwg.org/multipage/webappapis.html#event-loops
- MDN JavaScript guide and reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript
- MDN AbortController reference: https://developer.mozilla.org/en-US/docs/Web/API/AbortController
- React `useEffect` reference: https://react.dev/reference/react/useEffect
- Next.js Server and Client Components docs: https://nextjs.org/docs/app/getting-started/server-and-client-components
- web.dev RAIL performance model: https://web.dev/articles/rail

## Related Notes

- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[18 - Revision Plans/03 - 14 Day Deep Study Plan|14 Day Deep Study Plan]]
- [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]]
- [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]
- [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]
- [[01 - Roadmap|Roadmap]]
