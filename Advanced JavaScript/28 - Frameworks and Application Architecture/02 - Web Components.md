---
tags: [web-components, frameworks, web-platform]
module: "28 - Frameworks and Application Architecture"
priority: important
status: not-started
aliases: [Custom Elements, Shadow DOM]
---

# Web Components

## Maturity Target

- Priority: #important
- Study time: 40 minutes
- Interview signal: Name the three specs (custom elements, shadow DOM, templates), write a minimal custom element, and give a *fair* account of why frameworks won apps — plus where Web Components genuinely win.
- Production signal: You can consume a design-system web component from React without fighting it, and know when authoring one is the right call.
- Dependencies: [[28 - Frameworks and Application Architecture/01 - The Problem Frameworks Solve|The Problem Frameworks Solve]], [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]]

## Source Anchors

- [MDN - Web Components](https://developer.mozilla.org/en-US/docs/Web/API/Web_components)
- [web.dev - Custom elements best practices](https://web.dev/articles/custom-elements-best-practices)
- [Lit - documentation](https://lit.dev/docs/)

## 1. Concept

Simple version: Web Components are the *platform's* component model — a set of browser standards for defining your own HTML tags with encapsulated markup, style, and behavior. No library, no build step, works in any framework or none.

The three specs:

- **Custom elements** — `customElements.define('user-card', UserCard)` registers a class extending `HTMLElement`, with lifecycle callbacks: `connectedCallback` (inserted), `disconnectedCallback` (removed), `attributeChangedCallback` (observed attribute changed).
- **Shadow DOM** — `this.attachShadow({ mode: 'open' })` gives the element a private subtree with **style encapsulation**: outside CSS doesn't leak in, inside styles don't leak out. `<slot>` projects user-provided children into the shadow tree.
- **`<template>`/declarative shadow DOM** — inert markup for cloning; DSD (`<template shadowrootmode="open">`) enables *server-rendered* shadow trees.

```ts
class CopyButton extends HTMLElement {
  static observedAttributes = ['value'];
  #btn!: HTMLButtonElement;

  connectedCallback() {
    const root = this.attachShadow({ mode: 'open' });
    root.innerHTML = `<style>button{cursor:pointer}</style><button><slot>Copy</slot></button>`;
    this.#btn = root.querySelector('button')!;
    this.#btn.addEventListener('click', async () => {
      await navigator.clipboard.writeText(this.getAttribute('value') ?? '');
      this.dispatchEvent(new CustomEvent('copied', { bubbles: true, composed: true }));
    });
  }
}
customElements.define('copy-button', CopyButton);
// <copy-button value="npm i lit">Copy install command</copy-button> — works anywhere.
```

**The corrected history** (your brainstorm had the common misconception): Web Components did *not* precede-and-fail-into frameworks, nor did frameworks build on them. They evolved in parallel (v0 drafts ~2011, v1 shipped everywhere ~2018 — *after* React had won mindshare). And crucially, they solve a *different problem*: **encapsulation and interoperability of leaf widgets**, not the state→UI synchronization problem ([[28 - Frameworks and Application Architecture/01 - The Problem Frameworks Solve|previous note]]). A custom element still updates its internals imperatively — at app scale you'd reinvent a framework inside your elements (which is exactly what Lit provides: a tiny reactive-rendering layer *for authoring* them).

## 2. Why It Matters

- "Why didn't Web Components replace React?" is a favorite discriminator question — most candidates either dismiss WCs or overclaim them; the mature answer is "different problem."
- They're the standard answer for **framework-agnostic design systems**: one component library consumed by React, Angular, and Vue teams (Adobe Spectrum, Shoelace/Web Awesome, Material Web).
- React 19 finally ships first-class custom-element support (properties vs attributes handled correctly, typed events still manual) — removing the historical interop pain point, and making "how do WCs and React interact?" a current interview topic.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: your company's design system ships `<ds-select>` as a web component. The React app needs to pass an array of options and listen for selection.

```tsx
// Buggy (pre-React-19 habits): attributes only take strings
<ds-select options={optionsArray} onChange={handle} />
// → options becomes "[object Object]"; onChange never fires (the element
//   dispatches a custom 'ds-change' event, not React's synthetic change).
```

Trace: HTML *attributes* are strings; rich data must go through JS *properties* on the element instance. And custom elements communicate upward via `CustomEvent`s, which React's synthetic event system didn't auto-bind historically.

```tsx
// Fix (React 19: objects passed as properties automatically; events still need addEventListener or ref wiring)
function Select({ options, onSelect }: Props) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const el = ref.current!;
    const handler = (e: Event) => onSelect((e as CustomEvent<Option>).detail);
    el.addEventListener('ds-change', handler);
    return () => el.removeEventListener('ds-change', handler);
  }, [onSelect]);
  return <ds-select ref={ref} options={options} />;  // React 19 sets .options property
}
```

Tradeoffs: the wrapper restores type safety and idiomatic React at the cost of one adapter per component (design systems usually generate these). Shadow DOM encapsulation also means your app's Tailwind classes can't restyle internals — you style via the element's exposed CSS custom properties and `::part()`, which is *the feature working as designed*, not a bug.

> [!warning] Footgun: `composed: true` is required for a custom event to escape the shadow root. Forgetting it means the event fires but never reaches listeners outside the element — silent, maddening.

## 4. Interview Answer

Short answer:

> Web Components are three browser standards — custom elements for defining your own tags with lifecycle callbacks, shadow DOM for style and markup encapsulation, and templates/slots for composition. They excel at framework-agnostic, encapsulated widgets: one design-system component usable from React, Angular, or plain HTML. They didn't replace frameworks because they solve a different problem — encapsulation and interop, not state-to-UI synchronization. At app scale you still need a reactivity model, which is why even web-component authors use Lit.

Deeper answer:

> Fair-comparison depth: WCs win at longevity (platform API, no framework churn), interop, and true style isolation; they historically lost at SSR (fixed by declarative shadow DOM), rich-data passing (attributes are strings — properties solve it, React 19 finally maps them properly), and developer ergonomics versus JSX + devtools. The architectural reading: use a framework for the app shell and state flow; consider web components at the boundary — design systems, embeds/widgets running in unknown host pages, and micro-frontend seams.

## 5. Practice

1. <details><summary>Name the three specs and the one-line job of each.</summary>Custom elements — register new tags with lifecycle hooks; Shadow DOM — private, style-encapsulated subtree with slots; template/declarative shadow DOM — inert cloneable markup and SSR support for shadow trees.</details>
2. <details><summary>Why can't you pass an array via an HTML attribute, and what's the correct channel?</summary>Attributes are serialized strings by spec — an array coerces to a useless string. Rich data goes through element *properties* (el.options = [...]) set from JS; attributes are for primitive, declarative config. Well-built elements reflect between the two where sensible.</details>
3. <details><summary>Your `copied` CustomEvent fires (logged inside the element) but the page listener never runs. Two likely causes?</summary>(1) Missing `composed: true` — the event won't cross the shadow boundary; (2) missing `bubbles: true` — it won't propagate up to ancestors even in light DOM. Both must be set for shadow-DOM-internal dispatch to reach outside listeners.</details>

## Related Notes

- [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]]
- [[28 - Frameworks and Application Architecture/01 - The Problem Frameworks Solve|The Problem Frameworks Solve]]
- [[28 - Frameworks and Application Architecture/03 - Framework Approaches Compared|Framework Approaches Compared]]
- [[21 - React Internals and Patterns/10 - React 19|React 19]]
