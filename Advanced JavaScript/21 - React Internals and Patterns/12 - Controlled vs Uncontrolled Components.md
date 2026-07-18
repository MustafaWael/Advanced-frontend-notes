---
tags: [react, forms, patterns]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [Controlled, Uncontrolled]
---

# Controlled vs Uncontrolled Components

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can define both precisely (source of truth = React state vs the DOM), explain the render-per-keystroke cost, and the "changing from uncontrolled to controlled" warning.
- Production signal: you pick per form based on whether the UI must react to each keystroke, and you know when uncontrolled + FormData is the leaner choice.
- Dependencies: [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]], [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]

## Source Anchors

- [react.dev - Controlled and uncontrolled components (Sharing State)](https://react.dev/learn/sharing-state-between-components#controlled-and-uncontrolled-components)
- [react.dev - `<input>`](https://react.dev/reference/react-dom/components/input)
- [react.dev - Reacting to Input with State](https://react.dev/learn/reacting-to-input-with-state)
- [react.dev - You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)

## 1. Concept

The distinction is *where the input's current value lives*:

- **Controlled**: React state is the source of truth. The input's `value` is bound to state, and every change goes through `onChange` → `setState` → re-render. React and the DOM are kept in lockstep.
- **Uncontrolled**: the DOM is the source of truth. The input manages its own value; React reads it only when needed (via a ref or FormData at submit). You optionally seed it with `defaultValue`.

```jsx
// Controlled: state drives the input
const [name, setName] = useState("");
<input value={name} onChange={(e) => setName(e.target.value)} />

// Uncontrolled: the DOM holds the value; React reads on demand
const nameRef = useRef(null);
<input defaultValue="" ref={nameRef} />   // read nameRef.current.value at submit
```

## 2. Why It Matters

- Controlled inputs re-render the component **on every keystroke** — usually fine, but at scale (large forms, expensive siblings) it's a real cost, and the naive fix (memo everything) misses that uncontrolled inputs avoid the problem entirely.
- The "input changed from uncontrolled to controlled" warning is a top-5 React console error, and explaining it demonstrates you understand the model.
- React 19 form Actions + FormData ([[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]) revived uncontrolled forms as a first-class pattern — knowing when to use them is current, not legacy.

## 3. The Tradeoffs, Concretely

| | Controlled | Uncontrolled |
| --- | --- | --- |
| Source of truth | React state | DOM |
| Re-render per keystroke | Yes | No |
| Instant validation / formatting / conditional UI | Easy (you have the value) | Hard (value not in state) |
| Read value | Always available in state | On demand via ref/FormData |
| Reset | `setState("")` | `form.reset()` / key remount |
| Boilerplate | More (state + handler per field) | Less |

Rule of thumb: **controlled when the UI must react to each keystroke** (live validation, character counter, dependent fields, format-as-you-type, disabling submit on invalid). **Uncontrolled when you only need values at submit** (login, contact, filters) — leaner and no per-keystroke renders.

## 4. The Uncontrolled→Controlled Warning

React decides an input's mode on first render and won't let it switch. The usual cause is a `value` that starts `undefined` (uncontrolled) then becomes a string (controlled):

```jsx
// ❌ user starts undefined → value={undefined} = uncontrolled;
//    after fetch, user.name is a string → controlled. React warns.
<input value={user?.name} onChange={...} />

// ✅ always a defined string → controlled from the start
<input value={user?.name ?? ""} onChange={...} />
```

The mirror mistake is passing both `value` and `defaultValue`. The fix is almost always "coalesce to `""`": a controlled input's `value` must never be `null`/`undefined`.

> [!warning] value={0} and other falsy traps
> `value={count || ""}` breaks when `count` is `0` — a valid value that's falsy, so it renders empty. Use `value={count ?? ""}` (nullish, not `||`) so only `null`/`undefined` fall back. This is the [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|nullish vs falsy]] distinction biting inside forms.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a 40-field settings form where each field is controlled, and the whole form re-renders (plus an expensive preview panel) on every keystroke → typing feels laggy.

Buggy shape:

```jsx
function SettingsForm() {
  const [values, setValues] = useState(initial);   // one big object
  // every keystroke: setValues → SettingsForm re-renders → <ExpensivePreview> re-renders
  return (
    <>
      {fields.map(f => (
        <input key={f} value={values[f]} onChange={e => setValues(v => ({ ...v, [f]: e.target.value }))} />
      ))}
      <ExpensivePreview values={values} />
    </>
  );
}
```

Trace: each keystroke updates the shared `values` object → parent re-renders → 40 inputs + the preview reconcile every character. Even if inputs are cheap, `ExpensivePreview` isn't.

Production-safe fixes (choose by need):

- **If the preview doesn't need per-keystroke updates** → go uncontrolled + FormData; read on submit or on a debounced "preview" action. No per-keystroke renders at all:

```jsx
function SettingsForm() {
  function onSubmit(e) {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    save(values);
  }
  return (
    <form onSubmit={onSubmit}>
      {fields.map(f => <input key={f} name={f} defaultValue={initial[f]} />)}
      <button>Save</button>
    </form>
  );
}
```

- **If the preview must be live** → keep controlled but isolate the cost: memoize `ExpensivePreview` and feed it a *debounced* copy of values ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|or useDeferredValue]]), so it updates less often than the inputs. Or push state down so each field owns its own state and only the changed field re-renders.

Tradeoffs: uncontrolled sacrifices live validation and per-keystroke UI — adding those later means a controlled rewrite, so choose based on real requirements, not "controlled is the React way." Controlled-with-debounce keeps capabilities but adds memoization/debounce machinery and a slight lag in the derived UI. There's no universal winner; the axis is always "does the UI need each keystroke?"

## 6. Interview Answer

Short answer:

> Controlled means React state is the source of truth — `value` bound to state, `onChange` updates it, re-render per keystroke — which makes live validation and dependent UI easy. Uncontrolled means the DOM owns the value; you seed with `defaultValue` and read via ref or FormData at submit, avoiding per-keystroke renders. Controlled when the UI must react to each keystroke; uncontrolled when you only need values at submit.

Deeper answer:

> An input's mode is fixed on first render, so a `value` going from `undefined` to a string triggers the uncontrolled-to-controlled warning — fix by coalescing to `""`, using `??` not `||` so `0` survives. At scale, controlled forms re-render on every keystroke and can drag expensive siblings; remedies are uncontrolled+FormData, memoizing/debouncing the derived UI, or pushing state down per field. React 19 form Actions consuming FormData make uncontrolled forms a current first-class pattern, not a legacy fallback.

## 7. Practice

1. <details><summary>What triggers "A component is changing an uncontrolled input to be controlled," and the one-line fix?</summary>The input's `value` prop starts `undefined`/`null` (React infers uncontrolled) and later becomes a defined string (controlled) — commonly from async-loaded data. Fix: ensure `value` is always a defined string from the first render, e.g. `value={data?.field ?? ""}`. Never pass `undefined` to a controlled input's `value`, and don't mix `value` with `defaultValue`.</details>

2. <details><summary>`value={quantity || ""}` shows empty when the user types 0. Why, and the fix?</summary>`0 || ""` evaluates to `""` because `0` is falsy, so a legitimately-zero value renders blank. Use `value={quantity ?? ""}` — nullish coalescing falls back only for `null`/`undefined`, preserving `0`. This is the falsy-vs-nullish trap ([[12 - Advanced Language Concepts/04 - Truthy and Falsy|truthy/falsy]]) surfacing in a form.</details>

3. <details><summary>A 30-field form with a live-updating summary panel lags while typing. Enumerate three distinct fixes and their tradeoffs.</summary>(1) Uncontrolled + FormData, read on submit — kills per-keystroke renders but loses live summary. (2) Keep controlled, feed the summary a debounced/deferred value and `React.memo` it — keeps live-ish summary, adds debounce lag + machinery. (3) Push state down so each field owns its state and lift only what the summary needs — localizes re-renders but restructures the form. Pick based on whether the summary must be truly live and how much refactor is acceptable.</details>

4. <details><summary>When is uncontrolled strictly better, and when is it a trap?</summary>Better: forms needing values only at submit (login, search, filters, contact) — less code, no per-keystroke renders, and it composes with FormData/Server Actions. Trap: any requirement for per-keystroke behavior — live validation, character counters, format-as-you-type, fields that enable/disable others, controlled masking — since the value isn't in state you can't react to it, and retrofitting means a controlled rewrite. Decide by the interaction requirements up front.</details>

## Related Notes

- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]]
- [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
- [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms, Validation and Async Errors]] — the a11y contract for both controlled and uncontrolled inputs
