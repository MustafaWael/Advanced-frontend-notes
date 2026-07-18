---
tags: [react, internals, reconciliation, keys]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
aliases: [Keys, Diffing]
---

# Reconciliation and Keys

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can state React's diffing heuristics, explain exactly why index keys corrupt state, and reason about element type identity resetting state.
- Production signal: you can debug "the wrong input has focus / the wrong checkbox is checked after reordering" and fix it with correct keys.
- Dependencies: [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]], [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]

## Source Anchors

- [react.dev - Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)
- [react.dev - Rendering Lists](https://react.dev/learn/rendering-lists)
- [react.dev - Why does React need keys?](https://react.dev/learn/rendering-lists#why-does-react-need-keys)
- [react.dev - You Might Not Need an Effect (resetting state with a key)](https://react.dev/learn/you-might-not-need-an-effect)

## 1. Concept

Reconciliation is how React decides what changed between the previous element tree and the new one, so the commit phase mutates the minimum DOM. A naive tree-diff is O(n³); React uses **heuristics** to get O(n):

1. **Different element type at a position → destroy and rebuild.** `<div>` → `<span>`, or `ComponentA` → `ComponentB`, throws away the old subtree (DOM nodes, component state, effects) and mounts fresh.
2. **Same type → keep the instance, update props.** State and DOM node are preserved; only changed attributes are patched.
3. **Lists are matched by `key`**, not by position. Keys tell React "this is the *same* logical item, even if it moved."

The through-line: **identity determines whether state survives**. Position + type + key together define a component's identity across renders.

## 2. Why It Matters

Keys are the single most misunderstood React feature, and the bugs are subtle *state* bugs, not visual glitches: focus jumps, wrong checkboxes, form input tied to the wrong row after a sort or delete. This is a top-tier interview filter because the wrong-but-plausible answer ("keys are for performance / to silence the warning") is so common.

## 3. Why Index Keys Corrupt State

`key={index}` means "the item at position 0 is always the same item." When the list reorders/inserts/deletes, positions stay `0,1,2…` but the *data* at each position changed — so React keeps the old component instance (with its state) and just swaps the props.

```jsx
// Buggy: index keys on a reorderable/removable list
{todos.map((todo, i) => (
  <TodoItem key={i} todo={todo} />   // TodoItem has internal state: draft text, "expanded", focus
))}
```

Trace deleting the first of three items `[A, B, C]`:

1. Before: keys `0→A, 1→B, 2→C`. Suppose the user typed a draft into B's inline editor (B's local state).
2. Delete A. New data `[B, C]` → keys `0→B, 1→C`.
3. React matches by key: key `0` existed (was A's instance) → **reuses A's component instance**, now fed B's props. Key `1` (was B) → reused, fed C's props.
4. Result: B's draft text (stored in the instance formerly at key 0 = "A's" instance) now displays against… the wrong row; C shows B's stale local state; the last instance is unmounted, discarding C's state. Symptom: "deleting a row scrambled everyone's unsaved input."

Fix — stable identity from the data:

```jsx
{todos.map((todo) => (
  <TodoItem key={todo.id} todo={todo} />   // id follows the item wherever it moves
))}
```

Now key `todo.id` moves with the item, so React re-associates each instance with its true data; deleting A leaves B and C's instances (and state) intact.

> [!warning] Index keys are only safe when the list is static
> No reordering, no insertion/deletion except at the end, and items have no internal state or uncontrolled DOM state (focus, scroll, text selection). A render-only list of labels with index keys is fine. The moment items are stateful or the order can change, index keys are a latent state-corruption bug.

## 4. Element Type Identity Resets State

State preservation depends on the element being the *same type at the same tree position* across renders. Two traps:

```jsx
// ❌ Component defined inside another component: NEW function identity every render
function Parent() {
  function Child() { return <input />; }   // different Child on each Parent render
  return <Child />;                        // React sees a "new type" → remounts, input loses focus/value
}
```

```jsx
// ❌ Conditional structure changes the position/type
{isEditing ? <input /> : <input />}   // same type → state preserved (maybe surprising)
{isEditing ? <EditForm /> : <ViewCard />}  // different type → full remount (maybe desired)
```

Conversely, you can *intentionally* reset state by changing the key:

```jsx
<ProfileForm key={userId} user={user} />   // switching userId remounts the form → clears draft state
```

This "reset state with a key" pattern is React's official replacement for a `useEffect` that manually clears state when a prop changes.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a filterable list of expandable cards; each card tracks its own "expanded" boolean. Filtering reorders the visible items.

Buggy version uses `key={index}`; after filtering, the *wrong* cards appear expanded and an open card's scroll position lands on a different card. Root cause exactly as in section 3 — index keys reused instances against reshuffled data.

Fix: `key={card.id}`. Tradeoff and nuance:

- If items genuinely lack a stable id (e.g., a computed/derived list), you must *derive* one — a content hash or a composite of stable fields — rather than fall back to index. Fabricating `key={Math.random()}` is worse: it changes every render, forcing a full remount of the whole list (all state lost, all DOM rebuilt, focus destroyed) every time.
- Stable keys also unlock efficient reordering (React moves DOM nodes instead of rebuilding) — a real performance benefit, but correctness (state association) is the primary reason, not speed.
- If per-item state (expanded/draft) really shouldn't survive reordering, *lifting that state up* keyed by id, or storing it in a `Map<id, state>` in the parent, sidesteps the identity coupling entirely — sometimes the cleaner architecture ([[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|state design]]).

## Real-World Use Cases

### Uncontrolled inputs in an editable invoice: index keys scramble the DOM's own state

An invoice editor renders line items with uncontrolled inputs (`defaultValue`) for speed. Sorting the lines by amount reorders the data — but with index keys, React sees "same input at position 0" and never touches the DOM value the user typed.

```jsx
{lineItems.map((item, i) => (
  <tr key={i}>  {/* ❌ */}
    <td><input name="description" defaultValue={item.description} /></td>
    <td><input name="amount" defaultValue={item.amount} /></td>
  </tr>
))}
```

After sorting, each `<tr>` keeps its typed DOM value (React only sets `defaultValue`, which doesn't overwrite a dirty input) while the row now *represents* a different line item — the user's edits are silently attached to the wrong invoice lines. `key={item.id}` makes React move the DOM nodes with their items instead. This is the same identity rule as section 3, but the corrupted state lives in the **DOM** (value, focus, selection), not in component state — so even a "stateless" row component is unsafe with index keys.

> [!warning]
> Uncontrolled form state, focus, text selection, scroll position, and CSS animation progress are all per-DOM-node state. Index keys can scramble all of them without a single `useState` in sight.

### Replaying a CSS animation with a key change

A toast/notification system needs the slide-in animation to replay when a new toast replaces the current one. CSS animations run once per DOM node lifetime — updating props on the same node won't restart it.

```jsx
<div key={toast.id} className="toast-slide-in">{toast.message}</div>
```

Changing `key` changes identity → React unmounts the old node and mounts a fresh one → the browser runs the enter animation again. Deliberate use of heuristic 1/3: identity change forces a remount. Same trick remounts misbehaving third-party embeds (chart widgets, map instances) when their config changes: `<StripeCheckout key={accountId} />`.

### Composite keys when merging lists from multiple sources

A unified inbox merges emails and Slack messages. Both backends use numeric auto-increment ids, so `key={item.id}` collides — two different items claim the same identity, and React warns about duplicate keys or reuses the wrong instance.

```jsx
{inboxItems.map((item) => (
  <InboxRow key={`${item.source}:${item.id}`} item={item} />  // "email:42" vs "slack:42"
))}
```

Keys only need to be unique **among siblings**, but they must be unique there — a stable composite of source + id restores one-to-one identity. Same requirement appears with optimistic items: give a client-generated id (`crypto.randomUUID()` stored on the item at creation, not in render) so the row keeps its identity when the server id arrives.

> [!tip]
> Generate fabricated ids **once, at data-creation time**, and store them on the item. Generating them during render (`key={crypto.randomUUID()}`) is the `Math.random()` anti-pattern from Practice 2 — a new identity every render.

## 6. Interview Answer

Short answer:

> Reconciliation diffs the new element tree against the old with heuristics: different type at a position remounts the subtree; same type updates in place; list children are matched by `key`. Keys are about *identity* — they tell React which item is which across reorders. Index keys break this because positions are stable while the data at them isn't, so React reuses the wrong instances and their state.

Deeper answer:

> A component's identity is position + type + key, and identity decides whether state and DOM survive a render. Index keys are safe only for static, stateless lists; for anything reorderable or stateful, use an id that travels with the item. The same mechanism lets you *reset* state deliberately with `key={id}`, which replaces effect-based state clearing, and it explains why defining a component inside another remounts it every render — its type identity changes.

## 7. Practice

1. <details><summary>A form list uses `key={index}`. Users report: "I check a row's checkbox, delete a different row above it, and now the wrong row is checked." Explain precisely.</summary>The checkbox state lives in each row component instance (or as uncontrolled DOM state), keyed by index. Deleting an upper row shifts everything up, but React matches instances by index position — so the instance that held the checked state stays at its index and is now fed a different row's data. The check "moved" because state is bound to position, not to the item. Fix: `key={row.id}` so instances track their data.</details>

2. <details><summary>Why does `key={Math.random()}` "fix" a stale-display bug but destroy performance and focus?</summary>A fresh random key every render makes every item a "new" identity → React unmounts all old instances and mounts new ones each render: full DOM rebuild, all component state reset, effects re-run, focus/scroll/selection lost. It "fixes" stale display by nuking everything, which is why it feels like it works and is actually a severe anti-pattern. Use a stable, data-derived key.</details>

3. <details><summary>You want a profile edit form to discard unsaved changes whenever the selected user changes. Compare `useEffect(() => reset(), [userId])` with `key={userId}`.</summary>`key={userId}` remounts the form on user change, resetting *all* internal state cleanly with no effect, no missed fields, no extra render — React's recommended approach. The `useEffect` version is imperative, must enumerate everything to reset (easy to miss a field), and runs after an initial render with stale state (a flash). Keying is declarative and complete; the effect is error-prone. (Keep the effect approach only if you must reset *some* state but preserve other.)</details>

4. <details><summary>`{items.map(i => <><Row a={i}/><Divider/></>)}` warns about keys — where does the key go on a fragment?</summary>Use the explicit fragment form `<React.Fragment key={i.id}>…</React.Fragment>` — the shorthand `<>` can't take a key. The key belongs on the top-level element returned per iteration (the fragment), identifying the whole group, not on the children inside it.</details>

## Related Notes

- [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]
- [[21 - React Internals and Patterns/15 - Elements JSX and Component Identity|Elements JSX and Component Identity]]
- [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]
- [[01 - Roadmap|Roadmap]]
