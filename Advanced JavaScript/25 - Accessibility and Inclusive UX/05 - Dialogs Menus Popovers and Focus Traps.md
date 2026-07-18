---
tags: [accessibility, dialogs, focus-trap, popover]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
aliases: [modal, focus trap, popover API, inert]
verified_on: 2026-07-12
version_scope: "Baseline browser APIs (dialog, popover, inert) as of 2026"
---

# Dialogs, Menus, Popovers and Focus Traps

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: state the full modal contract (focus in, trap, Escape, restore, background inert) and know that `<dialog>` and the Popover API now implement most of it.
- Production signal: your overlays are operable and escapable by keyboard, and background content is truly inaccessible while a modal is open.
- Dependencies: [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Focus Management]], [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA]]

## Source Anchors

- [MDN: the dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog)
- [MDN: Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API)
- [MDN: inert attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/inert)
- [WAI-ARIA APG: Dialog (Modal) pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [WAI-ARIA APG: Menu pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)

## 1. Concept

**The modal dialog contract** (APG): when it opens, focus moves *into* it (first sensible element, or the dialog itself); while open, Tab cycles *within* it (focus trap) and everything behind is inaccessible to AT and keyboard (not just visually dimmed); Escape closes it; on close, focus *returns to the element that opened it*. Miss any clause and keyboard users either escape into a dimmed page they can't see, or close the dialog into `<body>`-limbo ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|focus crimes]]).

Historically this took a library. The platform now does the heavy lifting:

```tsx
function ConfirmDelete({ open, onClose, onConfirm }: Props) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (open) ref.current?.showModal();     // THE key call
    else ref.current?.close();
  }, [open]);

  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="confirm-title">
      <h2 id="confirm-title">Delete this project?</h2>
      <p>This cannot be undone.</p>
      <button onClick={onClose}>Cancel</button>
      <button onClick={onConfirm}>Delete</button>
    </dialog>
  );
}
```

`showModal()` (versus `show()` or just toggling CSS) buys: top-layer rendering (above all stacking contexts — no z-index war), background made **inert** (unfocusable *and* invisible to AT), focus moved in, Escape wired to `close`, and `::backdrop` for the dim. Focus restore to the invoker is also handled by the browser. What remains yours: labeling (`aria-labelledby`), sensible *initial* focus (`autofocus` on the least-destructive action for confirmations), and not breaking Escape.

**Popovers** (menus, date pickers, tooltips-with-content) are *non-modal*: no trap, light-dismiss (click-outside/Escape closes). The Popover API gives top-layer + light dismiss declaratively (`popover` attribute, `popovertarget` on the trigger — with the trigger relationship exposed to AT automatically). **Menus** specifically also need the APG keyboard pattern: `role="menu"`/`menuitem"`, arrow-key navigation (roving tabindex), `aria-expanded` + `aria-haspopup` on the trigger — and honesty: a nav dropdown is usually a *disclosure of links*, not a `menu` (that role implies application-menu semantics and keyboard behavior; misusing it burdens AT users with wrong expectations).

`inert` as a standalone attribute handles the cases `<dialog>` doesn't cover — e.g., an off-canvas drawer built without dialog: `<main inert={drawerOpen || undefined}>` makes the background truly dead instead of merely blurred.

## 2. Why It Matters

- Overlays are the most common completely-blocking a11y failure: an untrapped modal lets focus wander behind the dim where clicks land on invisible controls; an unrestorable close dumps users to the page top. These make flows *impossible*, not just unpleasant.
- The platform shift matters for engineering judgment: hand-rolled focus-trap code (the source of a decade of subtle bugs) is now mostly deletable in favor of `showModal()`/popover/inert — knowing this is current, senior-signal knowledge.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a hand-rolled modal from the design system's early days.

```tsx
// Bug: a styled div with a dim overlay
function Modal({ open, onClose, children }: Props) {
  if (!open) return null;
  return createPortal(
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        {children}
        <button className="x" onClick={onClose}>×</button>
      </div>
    </div>,
    document.body
  );
}
```

Trace the failures against the contract: focus never moves in (still on the trigger — Tab now walks the *background* behind the dim); nothing is inert (AT reads the whole dimmed page; clicks are blocked only by the overlay div, but keyboard and AT sail past); Escape does nothing; on close, focus is wherever it drifted; the × button is named "times" or nothing; the dialog has no role or label — AT users don't even know a dialog opened.

```tsx
// Fix: let the platform implement the contract
function Modal({ open, onClose, title, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { open ? ref.current?.showModal() : ref.current?.close(); }, [open]);

  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="modal-title"
            onClick={e => { if (e.target === ref.current) onClose(); }}>  {/* backdrop click */}
      <h2 id="modal-title">{title}</h2>
      {children}
      <button onClick={onClose} aria-label="Close">×</button>
    </dialog>
  );
}
```

Role (`dialog`), top layer, inert background, focus in, Escape, focus restore: all platform-provided. The remaining hand-wiring is labeling, the named close button, and backdrop-click (a UX choice — for destructive confirmations, consider *not* light-dismissing).

Tradeoffs: `<dialog>` needs its open/close driven imperatively from React state (the small effect above — or a library wrapper); deep customization of `::backdrop` animation and open/close transitions takes modern CSS (`@starting-style`, `transition-behavior: allow-discrete`); and if you support ancient browsers, you're back to a library (whose modern versions use dialog/inert internally anyway). For menus, the platform gives less — Popover API handles presentation and dismissal, but the arrow-key roving and `menuitem` semantics remain your code, so a maintained headless library (which implements APG) often beats hand-rolling.

> [!warning] The dim is not the barrier
> The single most common overlay bug: the background is visually dimmed but functionally alive — Tab reaches it, screen readers read it, and users act on controls they cannot see. Dimming is paint; **inertness** is the barrier. `showModal()` provides it; anything else must apply `inert` to the rest of the page explicitly.

## Real-World Use Cases

### Off-canvas mobile nav drawer made dead with `inert`

The hamburger menu slides a drawer over the page. It's not a `<dialog>` (the design wants it as part of the layout, animating from the edge), so nothing applies inertness for you — and the classic bug is Tab escaping the drawer into the dimmed page behind it.

```tsx
function AppShell({ children }: Props) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  return (
    <>
      <aside aria-label="Menu" data-open={drawerOpen}>
        <nav>…</nav>
        <button onClick={() => setDrawerOpen(false)}>Close menu</button>
      </aside>
      <div inert={drawerOpen || undefined}>   {/* header + main + footer */}
        {children}
      </div>
    </>
  );
}
```

Works because `inert` on the page wrapper is the same barrier `showModal()` erects: unfocusable, unclickable, invisible to AT — Tab now cycles the drawer naturally because there is nowhere else to go, no trap code required. You still owe Escape-to-close and focus restore to the hamburger button ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|focus placement]]).

> [!warning]
> `inert` must not cover the drawer itself — structure the DOM so the drawer is a sibling of the inert wrapper, not a child. Portaling the drawer out is the usual fix when it's nested ([[21 - React Internals and Patterns/16 - Synthetic Events and Portals|portals]]).

### "Copied!" share menu on the Popover API

A share button opens a small panel: Copy link, Twitter/X, LinkedIn. It's non-modal by nature — light-dismiss, no trap — which is precisely the Popover API's contract, declaratively:

```tsx
<button popoverTarget="share-menu">Share</button>
<div id="share-menu" popover="auto">
  <button onClick={copyLink}>Copy link</button>
  <a href={twitterUrl}>Share on X</a>
</div>
```

Works because `popover="auto"` gives top-layer rendering (no z-index war with the sticky header), Escape and click-outside dismissal, and the browser wires the trigger relationship (`aria-expanded`, details of the invoker) automatically. Note what it's *not*: no `role="menu"`, because this is a disclosure of mixed links/actions — the honest, cheaper semantics.

### Cookie consent: the judgment call between modal and non-modal

Legal wants a consent banner "users must interact with." Reaching for `showModal()` means nothing else on the page is operable until they answer — defensible for strict-consent jurisdictions, hostile everywhere else.

```tsx
// Non-modal: page stays usable, banner is reachable and labeled
<section role="region" aria-label="Cookie consent">
  <p>We use cookies …</p>
  <button onClick={acceptAll}>Accept all</button>
  <button onClick={rejectAll}>Reject all</button>
</section>
```

The mechanism being chosen here is *inertness itself*: modal = everything else dead; non-modal = an ordinary landmark in the tab order. Choose modal only when proceeding without an answer is genuinely not allowed — and if you do, the full contract applies (labeled dialog, focus in, Escape considered). A banner that visually blocks the page but isn't inert-backed is the worst of both: sighted users are stuck, keyboard users tab through a page they can't see.

### Toast over a modal: top-layer stacking

A settings `<dialog>` saves via a Server Action; the success toast renders in a portal to `document.body` — and appears *behind* the modal, because `showModal()` promoted the dialog to the top layer above every z-index.

```tsx
// Fix: make the toast container a popover so it joins the top layer too
<div id="toasts" popover="manual" role="status" className="sr-only-until-content">
  {toasts.map(t => <Toast key={t.id} {...t} />)}
</div>
// showPopover() on mount; popover="manual" = no light-dismiss, no focus moved
```

Works because the top layer is a separate stacking context ordered by promotion time — only other top-layer citizens (`dialog`, `popover`) can render above an open modal; no z-index value can. `popover="manual"` opts out of light-dismiss so the toast doesn't close the moment the user clicks in the dialog, and the announcement channel stays a live region ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|announcements]]).

## 4. Interview Answer

Short answer:

> A modal has a five-part contract: focus moves in on open; Tab is trapped inside; the background is inert — unfocusable and unreadable by AT, not just dimmed; Escape closes; and focus returns to the trigger on close. Today `<dialog>.showModal()` implements essentially all of it — top layer, inert background, Escape, focus handling — so my job reduces to labeling the dialog, choosing initial focus, and driving open/close from state. Non-modal overlays (menus, pickers) use the Popover API for top-layer and light-dismiss, with no trap — plus the APG arrow-key pattern if it's genuinely a menu.

Deeper answer:

> The historical bug surface was hand-rolled traps: enumerating focusable elements, wrapping Tab at the edges, forgetting the background — the dim-but-alive modal where keyboard users operate invisible controls is the canonical failure, and `inert` (as `showModal()` applies, or the attribute for custom drawers) is the actual barrier. Judgment calls that remain: initial focus on the least-destructive action in confirmations; whether backdrop-click dismisses (not for destructive flows); disclosure-of-links versus `role="menu"` honesty for nav dropdowns. I test the contract in component tests — open → focus inside; Escape → closed and trigger refocused; and one manual pass because focus behavior is exactly what jsdom approximates ([[24 - Testing and Quality/09 - Accessibility Testing|a11y testing]]).

## 5. Practice

1. <details><summary>Why must background content be inert rather than merely covered by an overlay div?</summary>The overlay intercepts *pointer* events only. Tab order and the accessibility tree don't know the overlay exists: keyboard focus walks the background controls (invisible under the dim), and screen readers read the entire page as if no modal opened. `inert` (via `showModal()` or the attribute) removes the background from focus, from AT, and from click targets — the semantic barrier matching the visual one.</details>

2. <details><summary>Where should initial focus go in: (a) a destructive confirm dialog, (b) a form dialog, (c) a long informational dialog?</summary>(a) The *non*-destructive button (Cancel) — Enter-by-reflex then does no harm; the APG explicitly endorses this. (b) The first field — the user came to fill it. (c) The dialog element itself (or its heading with `tabindex="-1"`) so AT announces the title and reading starts at the top, rather than focus landing on a Close button and skipping the content. The principle: focus lands where the user's next action or comprehension starts.</details>

3. <details><summary>A nav "Products" dropdown contains six links. `role="menu"` or disclosure? Argue it.</summary>Disclosure: a button with `aria-expanded` toggling a list of plain links. `role="menu"` claims application-menu semantics — AT switches interaction modes, users expect arrow-key roving, Enter activation, first-letter navigation, Escape-to-trigger; you'd have to implement all of it, and even done right it's the wrong mental model for "some links." The menu role fits menus of *actions* (Edit → Cut/Copy/Paste). Misused ARIA promises behavior that isn't there — worse than the humble, correct disclosure ([[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA rules]]).</details>

4. <details><summary>Write the component-test assertions for the full modal contract.</summary>Open: trigger click → `getByRole("dialog")` present; `expect(within(dialog).getByRole(...firstControl)).toHaveFocus()`. Label: `toHaveAccessibleName(title)`. Escape: `user.keyboard("{Escape}")` → dialog absent → `expect(trigger).toHaveFocus()` (restore!). Background: with dialog open, background button `expect(bgButton).not.toBeVisible()`-equivalent via inertness — in jsdom, assert `main` has the `inert` attribute if custom, or rely on a real-browser check for `showModal` since jsdom's dialog/inert support is partial ([[24 - Testing and Quality/06 - Integration vs End-to-End Tests|fidelity limits]]). The restore assertion catches the most common regression.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Keyboard Interaction and Focus Management]]
- [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA: Roles, Names and States]]
- [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|Synthetic Events and Portals]]
- [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing]]
