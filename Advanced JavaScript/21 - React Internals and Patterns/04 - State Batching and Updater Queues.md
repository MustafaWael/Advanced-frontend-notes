---
tags: [react, internals, state, batching]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
aliases: [Batching, Functional Updates]
---

# State Batching and Updater Queues

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: you can explain automatic batching (React 18), why multiple `setState(n+1)` collapse, and when to use functional updaters.
- Production signal: you never chase "my state is one update behind" bugs by adding effects; you reach for updater functions.
- Dependencies: [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]], [[03 - Scope and Variables/05 - Closures|Closures]]

## Source Anchors

- [react.dev - Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)
- [react.dev - State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [react.dev - useState](https://react.dev/reference/react/useState)
- [React 18 - Automatic batching](https://react.dev/blog/2022/03/29/react-v18#new-feature-automatic-batching)

## 1. Concept

**Batching**: React groups multiple state updates that happen in the same "tick" into a single re-render, instead of rendering once per `setState`. React 18 made this **automatic everywhere** — event handlers, promises, `setTimeout`, native event callbacks — via the concurrent renderer. (Pre-18, only React event handlers batched; async callbacks each triggered a separate render.)

```jsx
function handleClick() {
  setCount(c => c + 1);
  setFlag(true);
  setName("Ada");
  // React 18: ONE re-render with all three applied. Pre-18 in an async context: three renders.
}
```

**Updater queue**: when you call `setState`, you either pass a *value* (replace) or a *function* (an updater that receives the pending state). React enqueues these; at render time it applies them in order to compute the final state.

## 2. Why It Matters

- Batching is a performance feature you rely on implicitly (forms with many fields don't render per field).
- The value-vs-updater distinction is the mechanism behind the most common React gotcha — "I called setCount three times but it only went up by one" — and its correct fix. Getting this right separates people who understand [[21 - React Internals and Patterns/01 - Render and Commit Phases|state-as-snapshot]] from those who cargo-cult.

## 3. Why `setN(n + 1)` Three Times Adds One

`n` is a snapshot from the current render's closure ([[03 - Scope and Variables/05 - Closures|closures]]); it does not change mid-handler. So three calls all read the same `n`:

```jsx
const [n, setN] = useState(0);   // this render: n === 0
function bump() {
  setN(n + 1);   // enqueue: replace with 0 + 1 = 1
  setN(n + 1);   // enqueue: replace with 0 + 1 = 1
  setN(n + 1);   // enqueue: replace with 0 + 1 = 1
  // final queued state = 1 → one render, n becomes 1
}
```

Updater functions receive the *pending* accumulated state instead of the render snapshot, so they compose:

```jsx
function bump() {
  setN(prev => prev + 1);  // 0 → 1
  setN(prev => prev + 1);  // 1 → 2
  setN(prev => prev + 1);  // 2 → 3   → one render, n becomes 3
}
```

> [!tip] Rule of thumb: updater function whenever the next state depends on the previous
> Counters, toggles, appending to arrays/objects, anything computed from current state, and any setState inside async code (where the closed-over value may be stale). Pass a *value* only when the new state is independent of the old (`setName(inputValue)`).

## 4. Batching Boundaries

Batching groups updates within a synchronous execution span. Updates in *separate* tasks/awaits render separately:

```jsx
async function save() {
  setSaving(true);        // render 1 (this batch)
  await api.save(data);   // await = later microtask/task boundary
  setSaving(false);       // render 2 (new batch) — React 18 still batches EACH span, not across awaits
  setSaved(true);         // batched with the line above (same span)
}
```

The two updates after `await` batch together (both in the post-await span), but they can't batch with the pre-await `setSaving(true)` — that already rendered. To force updates *out* of a batch (rare — e.g. you must read the committed DOM between two updates), `flushSync(() => setX(...))` commits synchronously, at the cost of an extra render/reflow.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — rapid-fire updates from an event stream:

```jsx
function LiveTicker() {
  const [prices, setPrices] = useState([]);
  useEffect(() => {
    const es = new EventSource("/prices");
    es.onmessage = (e) => {
      // ❌ reads the `prices` snapshot from the render that ran this effect (likely []).
      setPrices([...prices, JSON.parse(e.data)]);
    };
    return () => es.close();
  }, []);                       // empty deps → effect closes over the FIRST render's prices
  return <Table rows={prices} />;
}
```

Trace: the effect runs once on mount, capturing `prices === []` forever. Every message does `[...[], newPrice]` → the list never grows past one item; you see only the latest price. This is a [[14 - JavaScript in React and Next.js/03 - Stale Closures|stale closure]] crossed with the snapshot rule.

Production-safe fix — functional updater reads the live pending state:

```jsx
es.onmessage = (e) => {
  setPrices(prev => [...prev, JSON.parse(e.data)]);  // no dependency on the render snapshot
};
```

Now the empty dependency array is *correct* — the updater doesn't close over `prices`, so it never goes stale, and each message appends to the true current array.

Tradeoff: unbounded `[...prev, x]` on a high-frequency stream grows without limit (memory) and re-renders a growing table on every tick — cap it (`prev.slice(-100)`), throttle/coalesce updates ([[04 - Functions Deep Dive/07 - Debounce and Throttle|throttle]]), and virtualize the table. The updater fixes *correctness*; volume management is a separate concern the same code must address.

## Real-World Use Cases

### Settings toggle that "sometimes doesn't work" on fast clicks

A notifications switch flips a boolean and fires a PATCH. Users double-click; the second click reads the same snapshot as the first, so the two updates cancel into a no-op — the same trap as `setN(n + 1)` twice, wearing a toggle costume.

```jsx
function NotificationsToggle({ save }) {
  const [enabled, setEnabled] = useState(false);
  function toggle() {
    setEnabled(!enabled);            // ❌ both rapid clicks enqueue "replace with true"
    save(!enabled);                  // ...and both PATCH the same value
  }
  // ✅ setEnabled(prev => !prev) — each queued updater flips the pending value
}
```

Two fast clicks in one batch: both handlers close over `enabled === false`, both enqueue `true` → the switch ends ON when the user expected OFF. The updater form composes (`false → true → false`). See [[03 - Scope and Variables/05 - Closures|Closures]].

### Chat: scroll to the new message with `flushSync`

"Send" must append a message *and* scroll the list to it — but the new message isn't in the DOM until React commits after the handler. Measuring right after `setState` scrolls to the old bottom.

```jsx
import { flushSync } from "react-dom";

function send(text) {
  flushSync(() => {
    setMessages(prev => [...prev, { id: crypto.randomUUID(), text }]);
  });                                    // DOM now contains the new message
  listRef.current.lastElementChild?.scrollIntoView({ behavior: "smooth" });
}
```

`flushSync` forces the render+commit synchronously, opting this update out of the batch so the next line reads the *committed* DOM. It costs an extra render and possible forced reflow — the rare legitimate use, per section 4.

> [!tip]
> Reach for `flushSync` only when you must read the committed DOM mid-handler (scroll-to-new-item, focus-the-new-input, print). For visual sync work that doesn't need to happen inside the handler, `useLayoutEffect` after the normal batch is cheaper ([[21 - React Internals and Patterns/07 - useLayoutEffect useInsertionEffect and Effect Timing|Effect Timing]]).

### Upload progress bar: batching across native callbacks

A file uploader sets progress from `xhr.upload.onprogress`, which can fire dozens of times per second. Under React 17 each native callback rendered separately; React 18's automatic batching groups the updates *within* one callback — but you still get one render per event.

```jsx
xhr.upload.onprogress = (e) => {
  setLoaded(e.loaded);
  setPercent(Math.round((e.loaded / e.total) * 100));  // React 18: batched with the line above
};
```

Batching solves "two states, one render" here; it does not throttle the event stream itself. If the progress bar still renders 60×/s, coalesce at the source (update only when the integer percent changes, or [[04 - Functions Deep Dive/07 - Debounce and Throttle|throttle]]) — same division of labor as the ticker example in section 5: batching is per-span correctness/efficiency, volume control is your job.

## 6. Interview Answer

Short answer:

> React batches state updates in the same execution span into one re-render — automatic everywhere as of React 18, including timeouts and promises. Passing a value to setState replaces state using the render's snapshot, so multiple `setN(n+1)` calls collapse to one increment; passing an updater `setN(prev => prev+1)` receives the pending state, so they compose. Use updaters whenever the next state depends on the previous or when setting state in async code.

Deeper answer:

> Because state is a per-render snapshot captured by closure, value-form updates all read the same stale `n`; the updater queue applies functions in order against accumulated state, which is why functional updates are the correct fix and adding effects is not. Batching boundaries follow synchronous spans — updates across an `await` render separately — and `flushSync` opts out when you must commit and read the DOM between updates, paying an extra render for it.

## 7. Practice

1. <details><summary>`setCount(count + 1); setCount(count + 1);` in a click handler where count is 5. Final value and number of renders?</summary>Final value 6, one render. Both calls read the same snapshot `count === 5` and enqueue "replace with 6"; the second overwrites the first with the identical value. React batches the handler into a single re-render. To reach 7 you'd need functional updaters (`prev => prev + 1` twice).</details>

2. <details><summary>Under React 18, do these two updates in a `setTimeout` cause one render or two? `setTimeout(() => { setA(1); setB(2); }, 100)`</summary>One render. React 18's automatic batching covers timeouts, promises, and native handlers — not just React events. (Under React 17 this would have been two separate renders, since batching there was limited to React event handlers.)</details>

3. <details><summary>A "select all" toggles 500 checkboxes by calling setState in a loop. Is this 500 renders? Should you worry?</summary>If the 500 setState calls happen in one synchronous span (e.g., one handler updating one state object, or many updates React batches), it's effectively one render — batching handles it. The anti-pattern is 500 *separate* state atoms each triggering work; prefer a single state structure (one array/set of selected ids) updated once with an updater, so it's one clean update and one render regardless of count.</details>

4. <details><summary>You must set state, then immediately measure the resulting DOM in the same handler. Why does a normal setState fail, and what's the tool?</summary>setState is asynchronous relative to your handler — the DOM isn't updated until React commits after the handler's batch, so measuring right after setState reads the *old* DOM. `flushSync(() => setState(...))` forces a synchronous commit so the DOM is updated before the next line, letting you measure. Cost: it breaks batching for that update (extra render + potential forced reflow), so use it only when you truly need the committed DOM mid-handler.</details>

## Related Notes

- [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[01 - Roadmap|Roadmap]]
