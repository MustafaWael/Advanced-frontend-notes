---
tags: [react, patterns, component-design]
module: "28 - Frameworks and Application Architecture"
priority: must-know
status: not-started
aliases: [Compound components, Composition over configuration]
verified_on: 2026-07-17
version_scope: "React 19"
---

# Component Design Patterns

## Maturity Target

- Priority: #must-know
- Study time: 50 minutes
- Interview signal: Name the failure mode compound components fix (prop explosion / configuration APIs), build one live (parent + context + subcomponents), and place it among the alternatives: children/slots, render props, headless hooks.
- Production signal: Your shared components stop accumulating boolean props; new layout requirements don't require new props; the design system's API survives its consumers' creativity.
- Dependencies: [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]], [[21 - React Internals and Patterns/11 - Custom Hook Design Patterns|Custom Hook Design Patterns]]

## Source Anchors

- [React - Passing Data Deeply with Context](https://react.dev/learn/passing-data-deeply-with-context)
- [Kent C. Dodds - Compound Components](https://kentcdodds.com/blog/compound-components-with-react-hooks)
- [Radix UI - Composition primitives](https://www.radix-ui.com/primitives/docs/overview/introduction)

## 1. Concept

Simple version: as a shared component gains users, its props multiply — `showIcon`, `iconPosition`, `renderFooter`, `hideCloseButton` — until it's a configuration language nobody can maintain. Compound components fix this by turning *props into structure*: instead of configuring one black box, consumers compose named parts in JSX.

The mechanism: a parent component owns shared state and provides it via context; child components (exposed as `Parent.Part` or named exports) consume that context. The consumer arranges the parts — *structure is the API*.

```tsx
// The pattern, minimal and runnable:
const TabsCtx = createContext<{ active: string; setActive: (v: string) => void } | null>(null);
const useTabs = () => {
  const ctx = useContext(TabsCtx);
  if (!ctx) throw new Error('Tabs.* must be used within <Tabs>'); // enforce the contract
  return ctx;
};

export function Tabs({ defaultValue, children }: { defaultValue: string; children: ReactNode }) {
  const [active, setActive] = useState(defaultValue);
  const value = useMemo(() => ({ active, setActive }), [active]);
  return <TabsCtx.Provider value={value}>{children}</TabsCtx.Provider>;
}
Tabs.List = ({ children }: { children: ReactNode }) =>
  <div role="tablist">{children}</div>;
Tabs.Trigger = ({ value, children }: { value: string; children: ReactNode }) => {
  const { active, setActive } = useTabs();
  return <button role="tab" aria-selected={active === value} onClick={() => setActive(value)}>{children}</button>;
};
Tabs.Panel = ({ value, children }: { value: string; children: ReactNode }) => {
  const { active } = useTabs();
  return active === value ? <div role="tabpanel">{children}</div> : null;
};

// Consumer: structure IS the configuration
<Tabs defaultValue="account">
  <Tabs.List>
    <Tabs.Trigger value="account">Account</Tabs.Trigger>
    <Tabs.Trigger value="billing">Billing <Badge>2</Badge></Tabs.Trigger>  {/* no `badgeProp` needed! */}
  </Tabs.List>
  <Tabs.Panel value="account"><AccountForm /></Tabs.Panel>
  <Tabs.Panel value="billing"><BillingTable /></Tabs.Panel>
</Tabs>
```

The neighboring patterns, and when each wins:

- **`children` / slot props** — simplest composition; enough when there's one hole to fill (`<Card footer={<X/>}>`).
- **Compound components** — multiple coordinated parts sharing implicit state; layout freedom for the consumer. Radix/Headless UI/shadcn are built on this.
- **Render props** — the component computes something and lets you render it: `<List renderItem={(x) => …}>`; today mostly niche (virtualized lists), largely displaced by…
- **Headless hooks** — *behavior without markup*: `useCombobox()` returns state + prop-getters, you own 100% of the DOM. Maximum control, most work.
- **Controlled ↔ uncontrolled duality** — mature compounds accept `value`/`onValueChange` *or* `defaultValue`, supporting both modes ([[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled]]).

## 2. Why It Matters

- "Design a reusable Modal/Tabs/Select" is a standard mid/senior practical — and the expected shape of the answer *is* this pattern (it's how every modern component library is built).
- Prop explosion is measurable API debt: each boolean prop doubles the state space; consumers block on library releases for layout tweaks that composition would have made free.
- The pattern showcases context used *correctly* — narrow, feature-scoped, memoized — versus the god-context anti-pattern ([[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

```tsx
// Buggy (organizationally): the design-system Select, 18 months in
<Select
  options={opts} label="Country" labelPosition="top" showSearch
  searchPlaceholder="Filter…" clearable clearIcon={<X/>} groupBy="region"
  renderOption={(o) => <Flag code={o.code} />} footerContent={<AddNew />}
  emptyState={<NoResults />} maxDropdownHeight={320} /* …23 more props */
/>
```

Trace: every consumer's novel layout became a prop. Props interact (`showSearch` × `groupBy` × `renderOption` = untested combinations); the component's internals are 60% conditional branches; feature requests queue on the DS team. This is the *configuration API death spiral* — the component absorbed its consumers' layout decisions.

```tsx
// Fix: recompose as compound parts (Radix-style)
<Select value={country} onValueChange={setCountry}>
  <Select.Trigger><Select.Value placeholder="Country" /></Select.Trigger>
  <Select.Content>
    <Select.Search placeholder="Filter…" />
    {regions.map(r => (
      <Select.Group key={r.id} label={r.name}>
        {r.countries.map(c => (
          <Select.Item key={c.code} value={c.code}><Flag code={c.code} /> {c.name}</Select.Item>
        ))}
      </Select.Group>
    ))}
    <Select.Footer><AddNew /></Select.Footer>
  </Select.Content>
</Select>
```

New layouts now need *zero* library changes — consumers rearrange parts. The 23 interacting props become ~6 focused components with 2–3 props each.

Tradeoffs, honestly: more verbose at every call site (the config version was one tag); consumers can now compose *invalid* structures (Trigger outside Select → the `useTabs`-style throw is your guard; nonsense orders need docs/lint); implicit context coupling is less discoverable than explicit props (TS helps less). Mitigation used by real design systems: ship the compound primitive *plus* a thin pre-composed convenience wrapper for the 80% case.

> [!warning] Footgun: forgetting to memoize the provider `value` makes every keystroke in `Select.Search` re-render every `Select.Item` through context. Compound components inherit all context performance rules ([[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics]]).

## 4. Interview Answer

Short answer:

> Compound components solve prop explosion. When a component's variations are expressed as props — showSearch, footerContent, renderOption — the prop count and their interactions grow until the component is an untestable configuration language. The compound pattern inverts it: a parent owns shared state and exposes it via context; named subcomponents consume it; and the consumer expresses layout as JSX structure instead of configuration. It's how Radix and Headless UI are built. The tradeoff is verbosity and the possibility of invalid compositions, which you guard with context-presence checks.

Deeper answer:

> Placing it in the pattern space: children/slots for single holes; compound components for coordinated multi-part widgets; headless hooks when the consumer should own all markup — behavior via prop-getters; render props surviving in niches like virtualization. Production-grade compounds also support controlled and uncontrolled modes, bake in ARIA roles and keyboard interaction at the part level, and memoize the context value. Organizationally, the pattern moves layout decisions from the library team to consumers — that's the actual payoff: the design system stops being a bottleneck.

## 5. Practice

1. <details><summary>What's the mechanical relationship between compound components and context, and the two rules that keep it healthy?</summary>The parent provides shared state via a feature-scoped context; parts consume it — that's what lets them coordinate without props through the consumer's JSX. Rules: memoize the provider value (context re-render semantics), and throw a descriptive error from the consuming hook when used outside the parent (enforce the composition contract).</details>
2. <details><summary>A teammate asks for `badgeOnSecondTab` prop on your Tabs. What does the compound pattern say?</summary>Nothing to add: the consumer writes `<Tabs.Trigger value="billing">Billing <Badge/></Tabs.Trigger>` — structure is the API, and arbitrary content composes into parts for free. The request itself is the signal you'd have been on the config-API death spiral.</details>
3. <details><summary>When do headless hooks beat compound components?</summary>When consumers need total markup/DOM control — custom design systems over shared behavior (useCombobox from Downshift), canvas-adjacent or highly bespoke UIs, or when styling systems conflict. You trade the compound's ready parts for prop-getters and wire the DOM yourself — maximum flexibility, most integration work.</details>

## Related Notes

- [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]]
- [[21 - React Internals and Patterns/11 - Custom Hook Design Patterns|Custom Hook Design Patterns]]
- [[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled Components]]
- [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|Accessibility and Inclusive UX MOC]]
