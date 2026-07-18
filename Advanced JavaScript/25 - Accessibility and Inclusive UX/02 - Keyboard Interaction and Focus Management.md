---
tags: [accessibility, keyboard, focus]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
aliases: [focus management, tab order, roving tabindex]
---

# Keyboard Interaction and Focus Management

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: explain tab order, `tabindex` semantics, roving tabindex, and where focus must go after UI transitions (open, close, delete, route change).
- Production signal: every feature you ship passes a keyboard-only walkthrough before review.
- Dependencies: [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]], [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]

## Source Anchors

- [MDN: Keyboard-navigable JavaScript widgets](https://developer.mozilla.org/en-US/docs/Web/Accessibility/Guides/Keyboard-navigable_JavaScript_widgets)
- [WAI-ARIA APG: Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
- [MDN: :focus-visible](https://developer.mozilla.org/en-US/docs/Web/CSS/:focus-visible)
- [WCAG 2.2: 2.1.1 Keyboard, 2.4.3 Focus Order, 2.4.7 Focus Visible](https://www.w3.org/WAI/WCAG22/quickref/?showtechniques=241#keyboard-accessible)

## 1. Concept

Keyboard users — screen-reader users, motor-impaired users, power users — operate the page through **focus**: exactly one element receives keystrokes at a time. Your job splits into four mechanics:

**Tab order.** Tab moves focus through interactive elements in *DOM order*. WCAG requires that order to be meaningful (2.4.3). Two implications: DOM order should match visual order (beware CSS reordering — `order`, `flex-direction: row-reverse`, absolute positioning — which changes what eyes see but not what Tab does), and `tabindex` has exactly two safe values: `0` (join the natural order — for custom widgets) and `-1` (programmatically focusable via `.focus()`, skipped by Tab — for headings, dialogs, error summaries). **Positive `tabindex` is a bug**: it hijacks global order and turns maintenance into whack-a-mole.

**Focus visibility.** Users must *see* where focus is (2.4.7). `outline: none` without replacement is the classic crime. Use `:focus-visible` — it shows the ring for keyboard focus while skipping it for mouse clicks, removing the aesthetic objection that motivated the crime:

```css
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
```

**Composite widgets: roving tabindex.** A toolbar/tab list/menu with 20 items must not be 20 tab stops (Tab-through-everything makes the page unusable). The pattern: the *container's active item* has `tabindex="0"`, all others `-1`; Arrow keys move activation (updating tabindex + `.focus()`); Tab enters and leaves the whole widget as one stop. This is what the [APG keyboard patterns](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) specify per widget.

**Focus placement after transitions.** Every UI transition must answer "where is focus now?": opening a dialog → into it ([[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|dialogs]]); closing → back to the trigger; deleting an item → the next item or list container; SPA route change → the new page's `h1` (with `tabindex="-1"`) or main region — because unlike full page loads, client-side navigation ([[19 - DOM and Browser APIs/11 - History and Navigation APIs|History API]]) doesn't reset focus, leaving it on a link that no longer exists while the screen reader says nothing.

## 2. Why It Matters

- Keyboard operability is the accessibility requirement that fails *loudest* in real audits and lawsuits — an unreachable button is a hard blocker, not a degraded experience.
- Focus management is invisible in mouse-based QA and code review. It only surfaces if someone actually tabs through the feature — which is why the manual pass ([[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|testing]]) is non-negotiable.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an inbox list where each row has a Delete button. A keyboard user deletes a message.

```tsx
// Bug: focus dies with the deleted row
function Row({ message, onDelete }: RowProps) {
  return (
    <li>
      <span>{message.subject}</span>
      <button onClick={() => onDelete(message.id)}>Delete</button>
    </li>
  );
}
```

Trace: focus was on the Delete button; the row unmounts; the browser drops focus to `<body>`. For a screen-reader user the world goes silent — no confirmation, position lost, and the next Tab starts from the top of the page. Repeat for each of 30 messages and the feature is effectively unusable.

```tsx
// Fix: decide where focus goes, then send it there
function Inbox() {
  const rowRefs = useRef(new Map<string, HTMLButtonElement>());
  const listRef = useRef<HTMLUListElement>(null);

  function handleDelete(id: string) {
    const ids = messages.map(m => m.id);
    const next = ids[ids.indexOf(id) + 1] ?? ids[ids.indexOf(id) - 1];
    deleteMessage(id);
    // After React commits the removal, move focus deliberately:
    requestAnimationFrame(() => {
      if (next) rowRefs.current.get(next)?.focus();     // next row's Delete button
      else listRef.current?.focus();                     // empty list: the container (tabindex={-1})
    });
  }
  // ... rows register their button refs in rowRefs
}
```

Pair it with an announcement ("Message deleted", [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live region]]) and the interaction is coherent: act → hear result → focus ready on the next action.

Tradeoffs: focus management is imperative code in a declarative framework — refs, timing (after commit: effects or rAF), and a map of row refs are real complexity. Concentrate it in reusable primitives (`useFocusOnDelete`, list components that own the policy) rather than sprinkling per feature. The alternative — skipping it — is invisible to your QA and disabling for keyboard users.

> [!warning] The three focus crimes
> 1. `outline: none` with no `:focus-visible` replacement — users can't see where they are (WCAG 2.4.7).
> 2. Positive `tabindex` — hijacks document-wide order; the fix is reordering the DOM, not out-numbering it.
> 3. Focus lost to `<body>` after unmounts (deleted rows, closed dialogs, route changes) — users restart from the page top. Every removal needs a focus destination.

## Real-World Use Cases

### Roving tabindex in a message-actions toolbar

A chat app puts React/Reply/Forward/Delete buttons on every message. With 50 messages on screen, naive markup means 200 tab stops — the page is unusable by keyboard. The toolbar pattern makes each message's actions one stop:

```tsx
function MessageActions({ actions }: Props) {
  const [active, setActive] = useState(0);
  const refs = useRef<HTMLButtonElement[]>([]);

  function onKeyDown(e: KeyboardEvent) {
    const delta = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!delta) return;
    const next = (active + delta + actions.length) % actions.length;
    setActive(next);
    refs.current[next]?.focus();          // move real focus, not just state
  }

  return (
    <div role="toolbar" aria-label="Message actions" onKeyDown={onKeyDown}>
      {actions.map((a, i) => (
        <button key={a.id} ref={el => { refs.current[i] = el!; }}
                tabIndex={i === active ? 0 : -1} onClick={a.run}>
          {a.label}
        </button>
      ))}
    </div>
  );
}
```

Works because the roving pair — `tabindex` swap plus `.focus()` — keeps exactly one entry point per widget: Tab jumps between messages, arrows move within one. Ship it once as a design-system primitive; tabs and menus reuse the same core ([[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|menus]]).

> [!warning]
> Updating only the state (`tabIndex`) without calling `.focus()` is the common half-implementation — the highlight moves visually but keystrokes still go to the old button.

### CSS-reordered pricing tiers where Tab jumps backwards

Marketing wants the "Pro" plan visually first on desktop, but "Free" first in the DOM for the mobile flow. Someone reaches for flexbox `order`:

```css
.tier--pro { order: -1; }   /* Pro renders first; DOM still says Free first */
```

Now Tab visits Free's CTA, then jumps *left* across the screen to Pro, then back right — and a screen reader reads a different sequence than the eyes see. Fails WCAG 2.4.3 because tab order follows **DOM order, not layout**. The fix is reordering the DOM (render the array differently per breakpoint, or restructure), never out-numbering it with positive `tabindex`.

### "Load more" pagination that strands focus

An article list ends in a Load More button. Clicking it appends 20 items — and in many implementations the button re-renders or moves, so focus falls to `<body>` and the keyboard user must Tab through everything from the top to reach the new content.

```tsx
async function handleLoadMore() {
  const firstNewId = await loadNextPage();
  requestAnimationFrame(() => {
    // Send focus to the first newly loaded item's link
    document.getElementById(firstNewId)?.querySelector("a")?.focus();
  });
}
```

Same mechanism as the delete case: every transition needs an explicit focus destination — here, the first *new* item, which also announces it. This is also the argument against replacing Load More with pure infinite scroll: scroll-triggered loading gives keyboard users no operable control and the footer becomes unreachable ([[19 - DOM and Browser APIs/06 - Observers|Observers]]).

### Global keyboard shortcuts that fight the focused input

A project-management app adds Gmail-style shortcuts: `c` creates a task, `/` focuses search. First bug report: users can't type the letter "c" in the task title field.

```tsx
useEffect(() => {
  function onKey(e: KeyboardEvent) {
    const t = e.target as HTMLElement;
    if (t.closest("input, textarea, [contenteditable], select")) return; // typing wins
    if (e.key === "/") { e.preventDefault(); searchRef.current?.focus(); }
    if (e.key === "c") openNewTask();
  }
  document.addEventListener("keydown", onKey);
  return () => document.removeEventListener("keydown", onKey);
}, []);
```

Works because keystrokes dispatch to the *focused element* and bubble up ([[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]) — a document-level listener must yield whenever focus sits in an editing context, or the shortcut layer becomes a keyboard trap for text entry.

> [!tip]
> Single-key shortcuts also need a way to disable or remap them (WCAG 2.1.4) — speech-input users trigger them with dictated words.

## 4. Interview Answer

Short answer:

> Keyboard support has four mechanics: a meaningful tab order (DOM order, with `tabindex` used only as 0 or −1 — positive values are a bug); visible focus via `:focus-visible`; roving tabindex inside composite widgets so a toolbar is one tab stop with arrow-key navigation; and deliberate focus placement after every transition — into an opened dialog, back to the trigger on close, to the next item after a delete, and to the new page's heading after SPA navigation, since client-side routing doesn't reset focus by itself.

Deeper answer:

> The subtle failures: CSS visual reordering (flexbox `order`, `row-reverse`) makes Tab jump around the screen because order follows DOM, not layout — WCAG 2.4.3; and unmount-driven focus loss silently dumps users to `<body>`, which mouse-based QA can never notice. In React this becomes imperative ref work timed after commit, so I centralize the policies in primitives — a list that owns "focus next item after delete," a dialog that owns trap-and-restore — instead of per-feature effects. Verification is a keyboard-only walkthrough per feature: reach everything, see focus everywhere, escape everything, never get lost.

## 5. Practice

1. <details><summary>Why is `tabindex="3"` worse than no tabindex at all?</summary>Positive values create a priority lane: all positive-tabindex elements (in numeric order) come before every naturally-ordered element, regardless of DOM position. One `tabindex="3"` reorders the whole document's tab experience, and every future interactive element silently sorts after it. The correct tool is DOM order itself; positive tabindex is a global side effect masquerading as a local fix.</details>

2. <details><summary>Design the keyboard behavior for a tab list (5 tabs above a panel).</summary>Per the APG tabs pattern: the tab list is one tab stop — the active tab has `tabindex="0"`, others `-1` (roving tabindex). Left/Right arrows move between tabs (wrapping), Home/End jump to first/last; activation either follows focus (simple content) or requires Enter/Space (heavy panels — deliberate choice). Tab from the active tab moves into the panel, not to the next tab. Roles: `tablist`/`tab`/`tabpanel` with `aria-selected` and `aria-controls` ([[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA]]).</details>

3. <details><summary>After a Next.js client-side navigation, what's the focus/announcement problem and the standard fix?</summary>A real page load resets focus to the document start and announces the new title; client-side navigation swaps content while focus stays on the old link (possibly unmounted → body) and nothing is announced — the user doesn't know the page changed. Fix: on route change, move focus to the new page's `h1` (`tabindex={-1}` + `.focus()`) or a skip-target in `<main>`, and ensure the document title updates (Next metadata does this; some setups add a route-announcer live region — Next includes one). Test it: tab, activate a link, and listen.</details>

4. <details><summary>A keyboard user reports they "can't get past the embedded code editor" on your docs page. What's the trap and the convention to fix it?</summary>The editor captures Tab (inserting a tab character), so Tab never leaves the widget — a keyboard trap (WCAG 2.1.2). Convention: Escape (or a documented key like Ctrl+M in CodeMirror/Monaco) toggles "Tab moves focus" mode, and the widget documents this to the user (visible hint or `aria-describedby`). Any widget that repurposes Tab must provide and communicate an exit.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs, Menus, Popovers and Focus Traps]]
- [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]]
- [[19 - DOM and Browser APIs/11 - History and Navigation APIs|History and Navigation APIs]]
- [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading States and Announcements]]
