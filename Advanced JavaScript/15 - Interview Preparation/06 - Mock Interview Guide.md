---
tags: [javascript, interview, mock-interview-guide]
module: "15 - Interview Preparation"
priority: important
status: not-started
---

# Mock Interview Guide

## Maturity Target

- Priority: #important
- Study time: repeat weekly
- Interview signal: can think aloud, recover from uncertainty, and structure answers under time pressure.
- Production signal: can reason from mechanisms to decisions instead of reciting memorized notes.
- Fast track: run one 45-minute session using the template below.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [React docs: Learn React](https://react.dev/learn)
- [Next.js docs: App Router](https://nextjs.org/docs/app)

## The STAR-M Framework

Use STAR-M for technical explanations:

| Step | Meaning | Prompt |
| --- | --- | --- |
| S | Simple answer | "In plain English..." |
| T | Technical mechanism | "The mechanism is..." |
| A | Applied example | "In frontend code..." |
| R | Risk or tradeoff | "The bug/tradeoff is..." |
| M | Mature close | "The safe pattern is..." |

Example for closures:

```text
Simple: A closure is a function that remembers variables from where it was created.
Technical: The function keeps a reference to its lexical environment.
Applied: In React, a timer callback can read state from the render that created it.
Risk: That becomes a stale closure if the component rerenders.
Mature close: Fix with dependencies, a functional update, or a ref depending on intent.
```

## Session Template: 45 Minutes

### 1. Warm-Up, 5 Minutes

Pick two easy questions:

- What is a closure?
- What is hoisting?
- What is the event loop?
- What is the difference between `let` and `const`?

Goal: get your voice moving, not prove anything.

### 2. Core Questions, 20 Minutes

Pick four questions from current weak areas. For each:

1. Read the question aloud.
2. Pause for up to 20 seconds.
3. Answer for two minutes using STAR-M.
4. Score yourself quickly.
5. Read the model answer only after your attempt.

Do not read model answers first. The skill is retrieval under pressure.

### 3. Code Output, 10 Minutes

Pick two code-output questions from Module 16.

Process:

1. Mark synchronous lines first.
2. Mark microtasks.
3. Mark tasks/timers.
4. Track bindings and closures.
5. State the output.
6. Explain why each line appears in that order.

Related: [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]], [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]

### 4. Practical Scenario, 5 Minutes

Pick one real frontend scenario:

- stale closure in React
- async race condition
- memory leak from listener cleanup
- hydration mismatch
- bundle size regression
- slow list rendering

Answer with: problem, likely cause, fix, tradeoff, verification.

### 5. Debrief, 5 Minutes

Write three notes:

- One answer that was strong.
- One mechanism you missed.
- One topic for the next session.

## Self-Scoring Rubric

Score each answer from 0 to 3:

| Dimension | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Accuracy | Wrong | Partly correct | Correct | Precise with edge cases |
| Structure | Rambling | Some order | Clear | Direct and polished |
| Mechanism | Missing | Vague | Named | Explained step by step |
| Application | None | Generic | Frontend example | Production tradeoff and fix |

Target:

- 8+ total: solid mid-level answer.
- 10+ total: strong mid-level answer.
- 11-12 total: senior-style answer for this topic.

If any dimension is 0 or 1, add the topic to the next session.

## Timing Versions

### 30-Second Version

Use when the interviewer asks for a brief answer.

```text
"A closure is a function that retains access to variables from the lexical scope where it was created. In React, this is why an effect callback can read values from the render that created it, so stale closures happen when dependencies or lifetimes are wrong."
```

### 2-Minute Version

Use for normal interview explanation.

Include:

- simple definition
- one mechanism term
- one code example
- one production bug
- one fix

### 5-Minute Deep Dive

Use only when asked to go deeper.

Include:

- full mechanism
- step-by-step trace
- edge case
- frontend production decision
- tradeoff between multiple fixes
- how you would verify the behavior

## Code Output Trace Method

Use this every time:

1. Write down initial global/module bindings.
2. Execute synchronous code top to bottom.
3. Track function calls and closures.
4. Queue microtasks from Promises and `queueMicrotask`.
5. Queue tasks from timers and events.
6. Drain microtasks before tasks.
7. State output in order.
8. Explain one line at a time.

Example:

```js
console.log('A');

setTimeout(() => console.log('D'), 0);

Promise.resolve()
  .then(() => {
    console.log('B');
    queueMicrotask(() => console.log('C'));
  });

console.log('E');

// Output: A, E, B, C, D
```

Reason:

- `A` and `E` are sync.
- Promise reaction logs `B` as a microtask.
- `queueMicrotask` inside that reaction queues `C` in the same microtask drain.
- Timer logs `D` in a later task.

## Recovery Scripts

### When You Need Thinking Time

```text
"Let me think through the execution order for a moment."
```

### When You Know The Area But Not The Exact Rule

```text
"I am not fully certain of the exact spec step, but I know this relates to __. My best reasoning is __. I would verify by __."
```

### When The Question Has Multiple Valid Answers

```text
"It depends on the ownership of the state. If it is server state, I would __. If it is local UI state, I would __. The tradeoff is __."
```

### When You Made A Mistake

```text
"Let me correct that. I said __, but the actual order is __ because __."
```

Recovering accurately is often more impressive than pretending you never miss.

## Weekly Plan

### Week 1: Runtime Foundations

Focus:

- execution context
- scope and lexical environment
- hoisting and TDZ
- closures
- `var`, `let`, `const`

Practice:

- [[15 - Interview Preparation/01 - Junior to Mid Questions|Junior to Mid Questions]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]
- [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]

### Week 2: Functions, `this`, Objects

Focus:

- function declarations vs expressions
- arrow functions
- `this` binding
- `call`, `apply`, `bind`
- prototypes and `new`

Practice:

- [[05 - this Binding/08 - this Checklist|this Checklist]]
- [[06 - Objects and Prototypes/08 - Objects Checklist|Objects Checklist]]
- [[16 - Code Output Questions/03 - this Output Questions|this Output Questions]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]

### Week 3: Async, Event Loop, Modules

Focus:

- Promise states
- microtasks and tasks
- async/await
- AbortController
- ES modules
- live bindings
- tree shaking

Practice:

- [[08 - Async JavaScript/08 - Async Checklist|Async Checklist]]
- [[09 - Event Loop Advanced/08 - Event Loop Checklist|Event Loop Checklist]]
- [[10 - Modules/08 - Modules Checklist|Modules Checklist]]
- [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]

### Week 4: React, Next, Performance

Focus:

- stale closures
- dependency arrays
- immutability
- async race conditions
- Server/Client Components
- hydration mismatch
- memory and performance

Practice:

- [[14 - JavaScript in React and Next.js/11 - React and Next Checklist|React and Next Checklist]]
- [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]

## Full Mock Interview Script

Use this once per week:

1. Explain closures.
2. Trace a closure code-output question.
3. Explain the event loop.
4. Trace a Promise/timer question.
5. Explain `this`.
6. Debug a React stale closure.
7. Fix a race condition in `useEffect`.
8. Explain Server vs Client Components.
9. Explain one performance issue you would measure.
10. Ask yourself: "What did I assume without proving?"

## Post-Mock Review Template

```text
Date:
Overall score:

Strong answers:
- 

Weak mechanisms:
- 

Code-output misses:
- 

Production examples to improve:
- 

Next session focus:
- 
```

## Related Notes

- [[15 - Interview Preparation/01 - Junior to Mid Questions|Junior to Mid Questions]]
- [[15 - Interview Preparation/02 - Mid Level Questions|Mid Level Questions]]
- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[15 - Interview Preparation/07 - Interview Checklist|Interview Checklist]]
