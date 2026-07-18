---
tags: [system-design, interview, component-api, design]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [props API, controlled uncontrolled, compound components, headless]
---

# Component API Design

## Maturity Target

- Priority: #must-know
- Study time: 50 minutes
- Interview signal: Design a reusable component's public API — props/events/slots, controlled vs uncontrolled, composition vs configuration — and justify each as a contract decision.
- Production signal: Your shared components are hard to misuse, support both controlled and uncontrolled use, and don't break consumers on internal refactors.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]

## Source Anchors

- [React — Sharing state / controlled components](https://react.dev/learn/sharing-state-between-components)
- [WAI-ARIA APG — Patterns](https://www.w3.org/WAI/ARIA/apg/patterns/)
- [Kent C. Dodds — Compound components](https://kentcdodds.com/blog/compound-components-with-react-hooks)

## 1. Concept

Simple version: RADIO's Interface phase has *two* APIs — the network API and the **component API** other developers consume. The component API is a contract: getting it wrong is a breaking change, unlike internal architecture you can refactor freely. That's why it's a distinct design step.

The decisions that define a component API:

- **Controlled vs uncontrolled** — does the consumer own the state (`value`/`onChange`) or does the component (`defaultValue`)? Mature components support **both**, like native inputs: controlled for when the parent needs the value, uncontrolled for drop-in simplicity.
- **Composition vs configuration** — a `renderItem` slot / `children` (composition) vs a `variant="..."` prop (configuration). Configuration is simpler for fixed cases; composition scales to variety without prop explosion.
- **Compound components** — `<Select><Select.Option/></Select>` share implicit state via context, giving flexible layout without a giant prop list.
- **Inversion of control** — inject behavior (`getSuggestions`, `filterFn`) so the component stays transport/policy-agnostic and testable ([[29 - Frontend System Design/02 - Designing an Autocomplete|Autocomplete]] does this).
- **Headless** — ship behavior + a11y + state, no markup; the consumer renders. Maximum flexibility, more consumer work.
- **Events and imperative escape hatches** — `onChange` vs `onValueCommit`; a `ref` handle (`focus()`, `scrollToItem()`) for the rare imperative need.

> [!warning] The controlled/uncontrolled footgun: switching a component from uncontrolled to controlled mid-life (passing `value={undefined}` then a string) throws React's "changing an uncontrolled input to controlled" warning and loses state. Decide ownership once; if supporting both, branch on whether `value` is provided at mount, not per render.

The clean way to support both is one small hook — controlled when `value` is passed, internal state otherwise, mode decided by whether `value` is defined:

```tsx
function useControllableState<T>(
  value: T | undefined,          // provided ⇒ controlled
  defaultValue: T,
  onChange?: (v: T) => void,
) {
  const [internal, setInternal] = useState(defaultValue);
  const isControlled = value !== undefined;
  const current = isControlled ? value : internal;
  const set = (next: T) => {
    if (!isControlled) setInternal(next);   // own the state only when uncontrolled
    onChange?.(next);                       // always notify the parent
  };
  return [current, set] as const;
}
```

The component reads `current` and calls `set` without caring which mode it's in — the same contract native inputs expose.

## 2. Why It Matters

A component API is the most expensive thing to change in a shared codebase — every consumer depends on it, so a bad prop shape becomes a migration. Interviewers use "design the component's props" to test whether you think in contracts (controlled state, composition, a11y guarantees) rather than just implementation. It's also the daily reality of building a design system.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a `<Modal isOpen title footerButtons variant size hideClose ...>` grew to 15 boolean/config props. Every new design needs another prop, and combinations conflict (a `variant="fullscreen"` that ignores `size`).

Trace: **configuration where composition was needed** — behavior varies on independent axes, so the flat prop list explodes combinatorially (the component-API version of the inheritance trap, [[31 - Low Level Design/03 - OOP Concepts|composition over inheritance]]).

```tsx
// Fix: compound + composition — layout is the consumer's, behavior/a11y is the component's
<Modal open={open} onClose={close}>
  <Modal.Header>Delete project?</Modal.Header>   {/* slots, not props */}
  <Modal.Body>This can't be undone.</Modal.Body>
  <Modal.Footer>
    <Button onClick={close}>Cancel</Button>
    <Button variant="danger" onClick={confirm}>Delete</Button>
  </Modal.Footer>
</Modal>
```

Tradeoff: compound components are more flexible but less discoverable (consumers must know the sub-components) and easier to assemble wrong (a `Footer` outside a `Modal`) — mitigate with TypeScript and runtime dev warnings. For a component with genuinely fixed structure, flat props are simpler; don't reach for compound reflexively.

## 4. Interview Answer

Short answer:

> A component API is a contract, so I design it separately from internals. The core decisions: support controlled and uncontrolled state like native inputs; prefer composition (slots, children, compound components) over a growing prop list when structure varies; invert control on policy like fetching or filtering so the component stays reusable and testable; and bake accessibility into the component so consumers can't forget it.

Deeper answer:

> The expensive mistakes are configuration-where-composition-was-needed — a prop explosion that turns every new design into a new prop — and leaking internal state ownership, which makes the controlled/uncontrolled boundary ambiguous. I decide ownership once and, if I support both, branch on whether `value` is provided at mount. For a design-system component I lean headless-plus-styled-wrapper: the headless core owns state, keyboard interaction, and the ARIA pattern, so every themed variant inherits correct behavior for free. The test I apply: can a consumer misuse this in a way that ships a bug? If yes, the API isn't done.

## 5. Practice

1. <details><summary>Why support both controlled and uncontrolled, and how do you implement it cleanly?</summary>Controlled lets a parent read/drive the value (validation, linked fields); uncontrolled is a zero-config drop-in. Implement by treating the component as controlled when `value` is passed and uncontrolled otherwise, deciding once at mount and keeping an internal state fallback — never flip modes mid-life or you lose state and trip React's warning.</details>
2. <details><summary>When is a headless component the right call over a fully-styled one?</summary>When many teams need the same behavior and a11y but different visuals (a design system across brands/products). Headless ships state + keyboard + ARIA and no markup, so each consumer styles freely without reimplementing correctness. The cost is more consumer work and less out-of-the-box; for a single app with one look, a styled component is faster.</details>
3. <details><summary>A prop list has grown to 15 props with conflicting combinations. What API change fixes it and what does it cost?</summary>Move to composition — slots/children or compound components — so structure comes from what the consumer nests, not from flags. It eliminates the combinatorial prop explosion but costs discoverability (consumers must learn the sub-components) and allows invalid assemblies, mitigated with types and dev-time warnings.</details>

## Related Notes

- [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]
- [[29 - Frontend System Design/02 - Designing an Autocomplete|Designing an Autocomplete]]
- [[31 - Low Level Design/04 - Design Patterns|Design Patterns]]
- [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]]
