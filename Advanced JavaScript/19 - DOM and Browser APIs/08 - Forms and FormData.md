---
tags: [javascript, dom, forms, react]
module: "19 - DOM and Browser APIs"
priority: important
status: not-started
aliases: [FormData]
---

# Forms and FormData

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain what native form submission does, how `FormData` serializes fields (and files), and why Next.js Server Actions and React 19 form actions are built on exactly this.
- Production signal: your forms survive JavaScript failing to load, and your file uploads don't hand-roll multipart encoding.
- Dependencies: [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]], [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]

## Source Anchors

- [MDN - FormData](https://developer.mozilla.org/en-US/docs/Web/API/FormData)
- [HTML Living Standard - Form submission](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-2)
- [MDN - Client-side form validation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation)
- [react.dev - form](https://react.dev/reference/react-dom/components/form)

## 1. Concept

A native form submission is browser behavior, not JavaScript: on submit, the browser collects every *successful* control (named, enabled fields; checked checkboxes/radios; selected file inputs), encodes them (`application/x-www-form-urlencoded` by default, `multipart/form-data` when files are involved), and navigates to the action URL with the result.

`FormData` is the JS object representation of that collection:

```js
form.addEventListener("submit", async (e) => {
  e.preventDefault();                    // take over from the browser
  const data = new FormData(form);       // reads current values from the DOM
  // data is multimap-like: .get, .getAll, .append, .set, .entries()
  await fetch("/api/apply", { method: "POST", body: data });
});
```

Key semantics:

- `new FormData(form)` snapshots the form *at that moment* — controls must have `name` attributes, and disabled controls are excluded (a classic "why is this field missing" bug: someone disabled the field to make it read-only; use `readonly` instead).
- It's a multimap: `getAll("tags")` for multi-selects/checkbox groups sharing a name.
- File inputs contribute `File` objects; passing FormData as a fetch body auto-sets `multipart/form-data` **with the boundary** — setting `Content-Type` manually breaks it.
- `Object.fromEntries(formData)` gives a plain object but silently drops duplicate names — fine for simple forms, wrong for checkbox groups.

## 2. Why It Matters

- The platform gives you serialization, validation, accessibility (Enter-to-submit, screen-reader semantics), and a no-JS fallback for free; hand-rolled `useState`-per-field forms silently discard all of it.
- **This API is having a renaissance**: React 19 form actions and Next.js Server Actions pass your function a `FormData` object — the platform primitive is the contract ([[21 - React Internals and Patterns/10 - React 19|React 19]], [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]). Progressive enhancement there literally *is* native form submission when JS hasn't hydrated yet.

## 3. Constraint Validation in One Pass

HTML attributes (`required`, `pattern`, `min`, `type="email"`) drive the built-in Constraint Validation API:

- Invalid controls block native submission and show browser UI.
- `form.checkValidity()` — silent boolean; `form.reportValidity()` — boolean + shows messages.
- `input.setCustomValidity("Passwords must match")` marks a control invalid with your message (empty string clears it) — this is how you plug custom rules into the native pipeline.
- CSS hooks: `:invalid`, `:user-invalid` (only after interaction — usually what you want).
- Escape hatch: `<form novalidate>` disables native UI while keeping the API queryable — the standard setup when a design system renders its own error messages.

## 4. Real Frontend Example: Bug → Fix → Tradeoff (File Upload)

Buggy version — JSON-brained upload:

```js
const [file, setFile] = useState(null);

async function onSubmit(e) {
  e.preventDefault();
  const base64 = await toBase64(file);      // FileReader dance
  await fetch("/api/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: file.name, data: base64 }),
  });
}
```

Traced failures:

1. Base64 inflates payload ~33% and the encode step materializes the whole file in memory — a 100MB video becomes ~133MB string on the main thread; the tab may crash.
2. Server must decode and buffer the JSON before touching the file — no streaming.
3. JSON body parsers commonly cap at 1MB — mystery 413s.

Production-safe fix — FormData end to end:

```jsx
async function onSubmit(e) {
  e.preventDefault();
  const data = new FormData(e.currentTarget); // includes <input type="file" name="attachment">

  const res = await fetch("/api/upload", {
    method: "POST",
    body: data,                // browser sets multipart/form-data; boundary included
    // DO NOT set Content-Type here
  });
  if (!res.ok) throw new HttpError(res);
}
```

Trace: the browser streams the multipart body — file bytes are read incrementally from disk, never fully decoded into a JS string; the server can stream to storage. Memory stays flat regardless of file size.

Tradeoffs: multipart parsing needs server support (Next.js route handlers expose `await request.formData()`); no upload progress from fetch — if you need a progress bar today you drop to `XMLHttpRequest`'s `upload.onprogress` or do chunked uploads; very large files should use resumable protocols (tus, S3 multipart) rather than one request.

> [!tip] Uncontrolled + FormData is the cheap-form pattern
> For forms that only need values at submit time (filters, login, contact), skip per-keystroke state entirely: uncontrolled inputs + `new FormData(form)` at submit. Fewer renders, less code, native validation intact. Reach for controlled inputs when the UI must react per keystroke ([[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled]]).

## 5. The React 19 / Server Actions Bridge

```jsx
// React 19 — the action receives FormData directly
function Signup() {
  async function signup(formData) {
    "use server";                       // Next.js Server Action
    const email = formData.get("email");
    await createUser({ email });
  }
  return (
    <form action={signup}>
      <input name="email" type="email" required />
      <button>Sign up</button>
    </form>
  );
}
```

Before hydration (or with JS disabled in the Server Action case), this submits as a *native form POST* — the framework encodes the action identity into the form. After hydration, React intercepts submit and calls the function with the same `FormData`. One mental model, both paths — which is precisely why knowing native form behavior became interview-relevant again.

## 6. Interview Answer

Short answer:

> Native submission collects named, enabled controls and encodes them as urlencoded or multipart. `FormData` is that collection as a JS multimap — construct it from a form, send it as a fetch body, and the browser handles encoding including file boundaries. Constraint Validation (`required`, `pattern`, `setCustomValidity`) gives validation without a library.

Deeper answer:

> Successful-control rules explain the classic bugs: missing `name` or `disabled` means the field vanishes; duplicate names need `getAll`, so `Object.fromEntries` is lossy. For uploads, multipart streams file bytes while base64-in-JSON buffers and inflates them. React 19 form actions and Next Server Actions receive `FormData` and degrade to native submission, so the platform behavior is the progressive-enhancement story.

## 7. Practice

1. <details><summary>A field shows on screen but never arrives at the server. List three attribute-level causes.</summary>(1) No `name` attribute — unnamed controls are never successful. (2) `disabled` — excluded from FormData/submission (use `readonly` to keep it submitted but uneditable). (3) An unchecked checkbox — contributes nothing at all (servers must treat absence as false). Bonus: the input sits outside the `<form>` without a `form="id"` association.</details>

2. <details><summary>Why does `fetch(url, { method: "POST", body: formData, headers: { "Content-Type": "multipart/form-data" } })` fail server-side?</summary>Multipart requires a unique `boundary` parameter in the Content-Type to delimit parts. When you set the header manually you omit the boundary the browser generated, so the server's parser can't split the body. Leave Content-Type unset; the browser writes `multipart/form-data; boundary=----WebKit...` itself.</details>

3. <details><summary>Checkbox group `name="tags"` with 3 boxes checked: compare `formData.get("tags")`, `getAll("tags")`, and `Object.fromEntries(formData)`.</summary>`get` returns only the first value; `getAll` returns all three (correct); `Object.fromEntries` keeps the *last* value per key, silently dropping two. Multi-value fields must go through `getAll` or careful entry iteration.</details>

4. <details><summary>How does a Next.js Server Action form work before hydration completes?</summary>The rendered HTML is a real `<form>` with POST semantics and an encoded action reference. Submitting triggers native browser submission to the server, which invokes the action with the parsed FormData and responds (typically re-rendering/redirecting). After hydration, React intercepts submit and performs the same call over fetch without navigation. That's progressive enhancement: the form is functional during slow loads and without JS.</details>

## Related Notes

- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled Components]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
- [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms, Validation and Async Errors]] — labels, error association, and announcements on top of native forms
