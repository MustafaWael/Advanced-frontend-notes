---
tags: [react, internals, jsx, elements]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [React Elements, JSX Transform, Element vs Component vs Instance]
---

# Elements, JSX and Component Identity

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can say what JSX compiles to, what a React element actually is (a plain object), and cleanly separate element vs component vs instance (fiber) — then use that vocabulary to explain remounting and key behavior.
- Production signal: you can predict when React will treat something as "a new component" (and destroy state) by reasoning about `type` identity, and you read component stacks / DevTools with the right mental model.
- Dependencies: [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]], [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Source Anchors

- [react.dev - createElement](https://react.dev/reference/react/createElement)
- [react.dev - Writing Markup with JSX](https://react.dev/learn/writing-markup-with-jsx)
- [Legacy React blog - React Components, Elements, and Instances](https://legacy.reactjs.org/blog/2015/12/18/react-components-elements-and-instances.html)
- [Dan Abramov - Why Do React Elements Have a $$typeof Property?](https://overreacted.io/why-do-react-elements-have-typeof-property/)

## 1. JSX Is a Compile-Time Transform

JSX is not HTML-in-JS and not part of JavaScript — it's syntax sugar that your build tool (Babel/SWC/TypeScript) compiles into plain function calls **before the browser ever sees it**:

```jsx
// You write:
<Button size="lg">Hi</Button>

// The automatic JSX runtime (React 17+) compiles it to:
import { jsx } from "react/jsx-runtime";
jsx(Button, { size: "lg", children: "Hi" });

// The older classic form (still what it conceptually means):
React.createElement(Button, { size: "lg" }, "Hi");
```

Consequences that follow immediately: JSX is optional (you could write the calls by hand), attributes are just object properties (hence `className`, `htmlFor`), `{expr}` slots are just arguments, and **children are ordinary values** — an element, an array, a string, a function. There is no template language; it's all JavaScript expressions producing objects.

## 2. An Element Is a Plain, Immutable Object

What those calls return is a **React element** — a cheap, plain JS object *describing* what you want on screen:

```js
console.log(<div className="box">hi</div>);
// {
//   $$typeof: Symbol.for('react.transitional.element'),  // 'react.element' before React 19
//   type: 'div',
//   key: null,
//   props: { className: 'box', children: 'hi' },
//   ref: null,   // (React 19: ref lives in props)
// }
```

An element is a *description*, not a live thing: creating one does nothing — no DOM, no component call, no lifecycle. It's the "order ticket," and rendering is the kitchen deciding what to cook. Elements are immutable and thrown away every render; this is exactly why they're cheap enough for the re-render-everything model ([[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]]).

> [!tip] Inspect the shape; don't program against it
> `type`, `props`, `key`, and `ref` are the useful concepts. `$$typeof` and the exact Symbol name are React implementation details that can change between releases, so use them to understand the safety boundary—not for feature detection, serialization, or application logic.

Two element `type` shapes matter: a **string** (`'div'`) means a host/DOM element; a **function reference** (`Button`) means a component to call. That's the whole reason **components must be capitalized**: JSX compiles `<button>` to the string `'button'` but `<Button>` to the identifier `Button` — lowercase it and React tries to create a DOM tag named after your component.

## 3. `$$typeof` — an XSS Defense Hiding in Plain Sight

Why the weird Symbol property? Security. If your server ever stores attacker-controlled JSON and your app renders `{message.text}`, an attacker could try to smuggle a *fake element object* into that data — `{"type":"div","props":{"dangerouslySetInnerHTML":{"__html":"<script>…"}}}`. React refuses to render any object whose `$$typeof` isn't the expected Symbol — and **JSON can't represent Symbols**, so data that ever crossed a JSON boundary can't forge it. (React 19 renamed the tag from `Symbol.for('react.element')` to `Symbol.for('react.transitional.element')` — which is also why some tools that hard-coded the old symbol broke on React 19.)

> [!warning] $$typeof is a safety net, not a license
> The check protects against *object injection through data*. It does nothing about the actual XSS holes in React apps: `dangerouslySetInnerHTML` with unsanitized input, and `href={userInput}` (`javascript:` URLs). Those remain your job ([[20 - Network and Security/05 - XSS|XSS]]).

## 4. Element vs Component vs Instance (Fiber)

Three words that get conflated constantly; separating them is the payoff of this note:

| Thing | What it is | Lifetime |
| --- | --- | --- |
| **Component** | The function (or class) — a *recipe* | Defined once at module scope |
| **Element** | `{ type, props, key }` — an *order ticket* describing one use of the recipe | Recreated every render, immutable |
| **Instance (fiber)** | React's internal record holding state, effects, DOM ref — the *dish being cooked* | Lives across renders, until unmount |

Reconciliation ([[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]) is precisely the matching step between the two ends: does this new *element* correspond to an existing *fiber* (same `type` reference at the same position, same `key`) → update the fiber in place, state survives. Different `type` → destroy the fiber (state and DOM gone), mount a new one.

"Same `type`" is a **reference comparison on the function object** ([[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]). Now the classic bug is mechanical, not mysterious:

```jsx
function Parent() {
  // ❌ a NEW function object is created on every Parent render
  function Child() { return <input />; }
  return <Child />;   // element.type !== previous element.type → unmount + remount
}
```

Every `Parent` render produces a different `Child` function, so the element's `type` never matches the previous fiber's — React unmounts and remounts, and the input loses its value and focus each keystroke. Hoist the component to module scope and the `type` reference is stable forever.

## 5. Real-World Payoffs

- **Children are just data.** `props.children` is a value you can count, wrap, or map (`Children.map`) — this is how layout components, slots, and "render prop" APIs work. No magic: you're passing objects and functions.
- **`React.memo`'s limits become obvious.** `<Card>{items.map(...)}</Card>` hands `Card` a *fresh children element array* every render, so memoizing `Card` on props does nothing — children are a prop with new identity. Memoize the content, not the wrapper.
- **DevTools and component stacks make sense.** The tree you inspect is fibers (instances); the props you see are from the latest matching elements; "the component rendered because props changed" means new elements whose props differ by `Object.is`.
- **`cloneElement` exists — and is discouraged.** It copies an element with merged props (`cloneElement(child, { extra })`). It made sense for injecting props into opaque children; it's now [marked legacy](https://react.dev/reference/react/cloneElement) because it makes data flow untraceable — prefer explicit props, context, or a render function.

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — a form field factory defined inside the form:

```jsx
function ProfileForm({ values, onChange }) {
  // ❌ redefined every render → new type identity → remount per keystroke
  const Field = ({ name }) => (
    <label>
      {name}
      <input value={values[name]} onChange={(e) => onChange(name, e.target.value)} />
    </label>
  );
  return (
    <form>
      <Field name="email" />
      <Field name="displayName" />
    </form>
  );
}
```

Trace: type one character → `onChange` → `ProfileForm` re-renders → a *new* `Field` function is created → the `<Field>` elements' `type` doesn't match last render's fibers → React unmounts both fields and mounts fresh ones → the focused input is destroyed mid-keystroke; focus and selection are lost, IME composition breaks, and (if fields were uncontrolled) their values vanish. The profiler shows mount/unmount, not update.

Production-safe fix — stable type identity:

```jsx
function Field({ name, value, onChange }) {   // ✅ module scope: same function reference forever
  return (
    <label>
      {name}
      <input value={value} onChange={(e) => onChange(name, e.target.value)} />
    </label>
  );
}

function ProfileForm({ values, onChange }) {
  return (
    <form>
      <Field name="email" value={values.email} onChange={onChange} />
      <Field name="displayName" value={values.displayName} onChange={onChange} />
    </form>
  );
}
```

Tradeoff and nuance: hoisting costs you the closure — `Field` must now receive `values`/`onChange` as props, which is more typing but *traceable* data flow. If you genuinely need per-render customization, pass a **render function** (`renderField={(name) => …}`) and *call* it — `{renderField("email")}` produces elements without introducing a new component `type`, so no remount. The rule: helper *called* during render (fine, it's just a function returning elements) vs helper *rendered as* `<Helper />` (a component — its identity now matters).

## 7. Interview Answer

Short answer:

> JSX compiles to `jsx(type, props)` calls that return React elements — plain immutable objects like `{ type, props, key, $$typeof }` that describe UI; nothing renders when you create one. Components are functions (recipes), elements describe one use of them (order tickets), and fibers are the live instances holding state. Reconciliation matches new elements to existing fibers by type reference, position, and key — which is why a component defined inside another remounts every render: its function identity changes, so React sees a new type.

Deeper answer:

> The `type` is a string for host elements ('div') and a function reference for components — that's the entire capitalization rule. `$$typeof` is a Symbol (renamed to `react.transitional.element` in React 19) that JSON can't forge, blocking element injection through server data — though real XSS defense is still sanitizing `dangerouslySetInnerHTML` and URLs. Practically, this model explains why memoizing a component with element children rarely helps (children are new objects each render), and the fix for inline-component remounts is hoisting or a called render function — a function *call* produces elements without creating a new component identity.

## 8. Practice

1. <details><summary>What does `console.log(<div className="box">hi</div>)` print, and what has rendered at that point?</summary>A plain object, roughly `{ $$typeof: Symbol(react.transitional.element), type: 'div', key: null, props: { className: 'box', children: 'hi' } }` (React 19 shape; `ref` lives in props now, and pre-19 the symbol was `react.element`). Nothing has rendered: creating an element performs no DOM work and doesn't call any component — it's a description that only does something if it ends up in a committed render ([[21 - React Internals and Patterns/01 - Render and Commit Phases|render/commit]]).</details>

2. <details><summary>Why must components be capitalized in JSX?</summary>The JSX compiler decides by the tag's first character: lowercase compiles to a *string* type (`jsx('button', …)` — a host/DOM element), capitalized compiles to the *identifier in scope* (`jsx(Button, …)` — your function). Write `<button>` for a component named `button` and React receives the string `'button'`, rendering a DOM tag and never calling your function. The convention isn't style — it's how the transform disambiguates host elements from components.</details>

3. <details><summary>How does `$$typeof` mitigate a class of XSS, and what does it NOT protect against?</summary>If attacker-controlled JSON is stored and later rendered as `{data}`, an attacker could embed an object shaped like a React element (e.g. with `dangerouslySetInnerHTML` in its props). React only renders objects whose `$$typeof` equals the element Symbol, and JSON cannot represent Symbols, so anything that crossed a JSON boundary fails the check. It does not protect against the real common holes: passing unsanitized HTML to `dangerouslySetInnerHTML` yourself, or `javascript:` URLs in `href`/`src` from user input — those need sanitization/validation.</details>

4. <details><summary>A memoized `<Layout>` re-renders every time its parent does, even though "nothing changed". It's used as `<Layout><Sidebar/><Main/></Layout>`. Explain via elements.</summary>`children` is a prop, and JSX creates *new* element objects for `<Sidebar/>` and `<Main/>` on every parent render — so `Layout`'s props always contain a fresh children array, `memo`'s shallow comparison fails, and it re-renders. Fixes: let the parent be the thing that skips rendering (memoize higher or move state down), hoist static children to a constant, or rely on the React Compiler which memoizes element creation. The insight: element identity, not "did anything visually change", drives props comparison.</details>

5. <details><summary>Element, component, instance — map each to what React Query's `useQuery` re-renders touch, or any concrete render you pick.</summary>Component: the function you wrote (`ProductList`) — never "re-created" by rendering. Element: `<ProductList category="x" />` — recreated as a new object by every parent render; cheap, immutable. Instance (fiber): the persistent record React keeps for that position — it holds the hook state (including `useQuery`'s cache subscription), survives re-renders, and is what "unmount" destroys. A re-render = call the component again, produce new elements, reconcile them against the existing fibers; state loss happens only when reconciliation decides an element no longer matches its fiber (type/key/position change).</details>

## Related Notes

- [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]
- [[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[20 - Network and Security/05 - XSS|XSS]]
- [[01 - Roadmap|Roadmap]]
