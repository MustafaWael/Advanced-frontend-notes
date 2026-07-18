---
tags: [accessibility, forms, validation]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
aliases: [accessible forms, error association]
---

# Accessible Forms, Validation and Async Errors

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: wire a field to its label, description, and error programmatically — and make async submission states perceivable without sight.
- Production signal: your forms are completable end-to-end with a screen reader, including the failure paths.
- Dependencies: [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]], [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]], [[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled]]

## Source Anchors

- [MDN: aria-describedby](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-describedby)
- [MDN: aria-invalid](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-invalid)
- [WAI Tutorials: Forms](https://www.w3.org/WAI/tutorials/forms/)
- [WCAG 2.2: 3.3 Input Assistance](https://www.w3.org/WAI/WCAG22/quickref/#input-assistance)

## 1. Concept

An accessible field is a set of **programmatic relationships**, not visual adjacency. Sighted users infer "this red text belongs to that input" from layout; AT users only get what the DOM declares:

```tsx
<label htmlFor="email">Email</label>
<input
  id="email"
  type="email"
  autoComplete="email"
  aria-describedby={
    [error && "email-error", "email-hint"].filter(Boolean).join(" ") || undefined
  }
  aria-invalid={error ? true : undefined}
/>
<p id="email-hint">We only use this for receipts.</p>
{error && <p id="email-error">{error}</p>}
```

The contract, piece by piece:

- **Label** — `<label htmlFor>` (or wrapping) gives the accessible name; placeholder is *not* a label (disappears on input, low contrast, not reliably announced).
- **Description** — `aria-describedby` attaches hints *and* errors; AT reads them after the name when the field is focused. Multiple ids space-separate.
- **Invalid state** — `aria-invalid` tells AT the field is in error; pair with visible styling that isn't color-only ([[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|color]]).
- **Autocomplete** — `autoComplete` tokens let browsers/password managers fill correctly (WCAG 1.3.5) and reduce typing for motor-impaired users.

**Async submission** adds the time dimension — pending, success, and failure must be *perceivable* ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|announcements]]):

- Pending: keep the submit button *enabled but guarded* (or if disabling, announce why); reflect state in text ("Saving…"), not spinner-only.
- Server errors: render a **focusable error summary** at the top (`tabindex={-1}`, `role="alert"` or moved-to focus), listing links to each invalid field; also wire per-field `aria-describedby`/`aria-invalid`. Move focus to the summary — that's both the announcement and the navigation.
- Success: announce it (live region or focus to a confirmation heading), don't just morph the button.

React 19/Next form Actions (`useActionState`) return errors as state — the same wiring applies; progressive enhancement means the no-JS fallback re-renders with errors server-side ([[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]).

## 2. Why It Matters

- Forms are where users *must* succeed — signup, checkout, support. An inaccessible marketing page loses a reader; an inaccessible form loses a customer and invites legal exposure.
- The async failure path is the least-tested, most-broken part: a visually-rendered error that is never announced leaves a screen-reader user submitting into silence — the exact bug class from [[24 - Testing and Quality/09 - Accessibility Testing|accessibility testing]] that automation can't see.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a checkout form. Validation errors appear on submit; a screen-reader user reports "nothing happens when I press Pay."

```tsx
// Bug: errors exist only visually
function CheckoutForm() {
  const [errors, setErrors] = useState<Errors>({});
  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const errs = validate(fields);
    setErrors(errs);                       // red text renders... silently
    if (!Object.keys(errs).length) await pay(fields);
  }
  return (
    <form onSubmit={onSubmit} noValidate>
      <input placeholder="Card number" />                    {/* placeholder-as-label */}
      {errors.card && <span className="err">{errors.card}</span>}  {/* unassociated */}
      <button disabled={pending}>Pay</button>                {/* disabled = unfocusable = silent */}
    </form>
  );
}
```

Trace: focus stays on Pay after submit; the new red text is off-screen for AT (nothing announced, nothing focused); the input has no accessible name (placeholder) and no `aria-invalid`/`aria-describedby`, so even tabbing to it reads just "edit text." During pending, the disabled button drops out of the tab order — focus falls to body mid-interaction.

```tsx
// Fix: summary-with-focus + associated fields + perceivable pending state
function CheckoutForm() {
  const summaryRef = useRef<HTMLDivElement>(null);
  const [state, formAction, pending] = useActionState(payAction, initial);

  useEffect(() => {
    if (state.errors) summaryRef.current?.focus();          // announce + navigate in one move
  }, [state]);

  return (
    <form action={formAction} noValidate>
      {state.errors && (
        <div ref={summaryRef} tabIndex={-1} role="alert" aria-labelledby="err-heading">
          <h2 id="err-heading">There are {Object.keys(state.errors).length} problems</h2>
          <ul>{Object.entries(state.errors).map(([id, msg]) =>
            <li key={id}><a href={`#${id}`}>{msg}</a></li>)}
          </ul>
        </div>
      )}
      <label htmlFor="card">Card number</label>
      <input id="card" autoComplete="cc-number" inputMode="numeric"
             aria-invalid={!!state.errors?.card || undefined}
             aria-describedby={state.errors?.card ? "card-error" : undefined} />
      {state.errors?.card && <p id="card-error">{state.errors.card}</p>}

      <button aria-disabled={pending}>{pending ? "Processing…" : "Pay"}</button>
    </form>
  );
}
```

Notes on the choices: `aria-disabled` keeps the button focusable and announceable during pending (guard re-submission in the handler) — hard `disabled` yanks focus; the summary's `tabindex={-1}` + `.focus()` makes the failure both heard and actionable (each link jumps to its field); error text also renders per-field with association so fixing one field re-reads its own error.

Tradeoffs: this is more DOM and state plumbing than the naive version — the pattern belongs in your form primitives (a `<Field>` component owning id/label/describedby wiring; a `<FormErrorSummary>`), written once. Native browser validation (`required`, `type=email` without `noValidate`) gets you bubbles and focus for free but with inconsistent styling and messaging; custom validation buys design control at the cost of reimplementing the announcement contract — which is exactly what this pattern is.

> [!warning] Placeholder is not a label, disabled is not a state
> The two recurring form crimes: placeholder-as-label vanishes the moment the user types (and was never a reliable accessible name), and `disabled`-during-pending silently ejects keyboard users from the control they just activated. Label with `<label>`; keep the button focusable with `aria-disabled` + a text change, or manage focus explicitly.

## Real-World Use Cases

### Shipping options as a real radio group with `fieldset`/`legend`

A checkout step offers Standard/Express/Overnight as styled cards. Built as clickable divs, AT users get three unlabeled clickables with no indication they're mutually exclusive — or what the group is even asking.

```tsx
<fieldset>
  <legend>Shipping method</legend>
  {options.map(opt => (
    <label key={opt.id} className="shipping-card">
      <input type="radio" name="shipping" value={opt.id}
             checked={selected === opt.id} onChange={() => setSelected(opt.id)} />
      <span>{opt.label}</span> <span>{opt.price}</span>
    </label>
  ))}
</fieldset>
```

Works because `fieldset`/`legend` is the programmatic version of "these belong together": focusing any radio announces the legend ("Shipping method"), arrow keys move within the group as one tab stop, and `name` enforces exclusivity — the group relationship exists in the DOM, not just the visual card layout ([[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML]]). Style the cards via the label; the radio can be visually hidden but must stay focusable (no `display: none`).

### Password field with live requirements checklist

Signup shows "8+ characters, one number, one symbol" as a checklist that ticks off while typing. Visually clear; programmatically it needs to be the field's *description*, not decorative siblings.

```tsx
<label htmlFor="pw">Password</label>
<input id="pw" type="password" autoComplete="new-password"
       aria-describedby="pw-rules" aria-invalid={submitted && !allMet || undefined} />
<ul id="pw-rules">
  {rules.map(r => (
    <li key={r.id}>
      <span aria-hidden="true">{r.met ? "✓" : "✗"}</span> {r.label}
      <span className="sr-only">{r.met ? " — met" : " — not met"}</span>
    </li>
  ))}
</ul>
```

Works because `aria-describedby` attaches the whole checklist to the field: on focus, AT reads the requirements after the name. The met/not-met state rides in text (sr-only), not icon color alone. Don't wire the checklist as a live region — it would announce on every keystroke; the settled check on blur/submit is the announced event ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|choreography]]).

### Multi-step checkout wizard: focus and errors per step

A four-step wizard (cart → address → payment → review) swaps its content client-side. Two recurring failures: step changes are silent (focus stays on the clicked Next button, now possibly gone), and "step 2 of 4" exists only as a progress graphic.

```tsx
function Step({ index, total, title, children }: StepProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => { headingRef.current?.focus(); }, [index]);   // each step change

  return (
    <section aria-labelledby={`step-${index}`}>
      <h2 id={`step-${index}`} ref={headingRef} tabIndex={-1}>
        Step {index} of {total}: {title}
      </h2>
      {children}
    </section>
  );
}
```

Works because a step change is an SPA transition in miniature: nothing resets focus for you, so the heading (with `tabindex={-1}`) becomes the landing point, and putting "Step 2 of 4" *in the heading text* makes position announce for free ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|focus placement]]). Validation stays per-step: the error summary pattern runs inside the step, blocking Next — never save all errors for a final-step dump.

> [!warning]
> Don't block Back/step-navigation while the current step is invalid — trapping users in a step they can't complete (card declined, address not found) with no exit is a keyboard trap at the flow level.

## 4. Interview Answer

Short answer:

> An accessible field is programmatic relationships: `<label htmlFor>` for the name, `aria-describedby` linking hints and errors, `aria-invalid` for state, `autoComplete` for fill assistance. For async submission, the failure path must be perceivable: a focusable error summary that receives focus on failure (announcing and enabling navigation via links to fields), per-field association so each error re-reads with its input, and a pending state that stays focusable — `aria-disabled` with changed text, not hard `disabled` that drops keyboard users to body.

Deeper answer:

> Visual adjacency communicates nothing to AT — every "this text belongs to that field" needs an id-relationship in the DOM. The async dimension is where teams fail: errors render but nothing moves focus and nothing announces ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live regions]] or focus-to-summary solve it), success morphs a button silently, and pending states disable the very control holding focus. With React 19 Actions the same wiring hangs off `useActionState`, and progressive enhancement gives a no-JS fallback where the server re-renders with the same associations ([[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]). I pin the contract in component tests: `toHaveAccessibleDescription(/error/)`, `toBeInvalid`, and focus assertions after a failing submit.

## 5. Practice

1. <details><summary>Why does the error summary get `tabIndex={-1}` and `.focus()` instead of relying on `role="alert"` alone?</summary>`role="alert"` announces the content once, but leaves focus where it was — the user hears the errors then must hunt for them. Focusing the summary does both jobs: screen readers announce the focused region, and the user is *positioned* at the list of links to broken fields. `tabindex="-1"` makes a non-interactive div focusable programmatically without adding it to tab order ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|focus management]]). Belt and suspenders: keep `role="alert"` for AT that announces on render.</details>

2. <details><summary>When is native HTML validation (no `noValidate`) the right call, and when do you take over?</summary>Native (`required`, `type`, `min/maxLength`, `pattern`): free focus-to-first-invalid, free announcements, zero JS, works pre-hydration — right for simple forms where default bubbles' styling/wording is acceptable. Take over (add `noValidate`, custom logic) when you need: consistent styled messages, cross-field rules, async/server checks (username taken), or an error-summary UX. Taking over means you now own everything native did: association, focus movement, announcement — the whole pattern above. Half-measures (custom visuals, no wiring) are the bug.</details>

3. <details><summary>A username field validates availability against the server as the user types. Design the announcement behavior without spamming.</summary>Debounce the check ([[17 - Practical Frontend Scenarios/09 - Debounced Search|debounced search]]); report the *settled* result via a polite live region or `aria-describedby` text update — "Username available" / "Username taken, try another" — never per-keystroke. Set `aria-invalid` only when settled-invalid (not mid-check). Mark the checking state visually and with text ("Checking…") but keep it out of assertive announcements. On submit, the summary pattern still applies if stale. Politeness level is the design decision: progress is polite-or-silent, outcomes are polite, failures blocking submission are the summary's job.</details>

4. <details><summary>How do you test this form contract so a refactor can't silently drop it?</summary>Component tests ([[24 - Testing and Quality/03 - React Component Testing Through User Behavior|RTL]]): submit invalid → `expect(summary).toHaveFocus()`, links point at field ids; field: `toBeInvalid()`, `toHaveAccessibleDescription(/card number/i)`; pending: button still focusable, has "Processing…" name; success: confirmation announced/focused. Plus axe for the static rules and one manual screen-reader pass to hear the actual flow ([[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|manual checks]]). The focus and description assertions are the ones that catch real regressions — they encode the relationships.</details>

## Related Notes

- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading States and Announcements]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing]]
