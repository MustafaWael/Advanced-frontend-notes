---
tags: [nextjs, server-actions, security, forms]
module: "22 - Next.js Deep Dive"
priority: must-know
status: not-started
aliases: [Server Actions, Server Functions]
verified_on: 2026-07-12
version_scope: "Next.js 14–16, React 19"
---

# Server Actions

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can explain the serialization boundary, the security model (they're public endpoints), and progressive enhancement.
- Production signal: you validate and authorize every Server Action as an untrusted entry point and use them with React 19 form Actions.
- Dependencies: [[21 - React Internals and Patterns/10 - React 19|React 19]], [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]], [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]

## Source Anchors

- [Next.js - Updating Data (Server Functions)](https://nextjs.org/docs/app/getting-started/updating-data)
- [React - Server Actions](https://react.dev/reference/rsc/server-actions)
- [React - use server directive](https://react.dev/reference/rsc/directives/use-server)
- [Next.js - Security and Server Actions](https://nextjs.org/blog/security-nextjs-server-components-actions)

## 1. Concept

A Server Action is an async function marked `"use server"` that runs **on the server** but can be **called from client code** — including passed as a `<form action={...}>` or invoked from an event handler. Next.js and React handle the RPC: the client gets a *reference* to the function; calling it sends a request to the server, which executes the real function and returns the (serialized) result.

```tsx
// Server Action (own file or inline in a Server Component)
async function createTodo(formData: FormData) {
  "use server";
  const title = formData.get("title");
  await db.todo.create({ data: { title } });
  updateTag("todos"); // Next 16: immediate read-your-writes for this action
}

// Used directly as a form action — no manual fetch, no API route
<form action={createTodo}>
  <input name="title" />
  <button>Add</button>
</form>
```

This collapses the traditional "write an API route + client fetch + wire up loading/error" into one function, and it integrates with React 19 Actions ([[21 - React Internals and Patterns/10 - React 19|useActionState/useOptimistic]]).

### After the mutation: which freshness call?

A Server Action that writes data almost always needs to tell a cache. The Next 16 decision (see [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]] for the full table):

- `updateTag(tag)` — the user must immediately see their own write (form submit → updated list). Server-Action-only.
- `revalidateTag(tag, "max")` — other visitors can briefly see stale data while it refreshes (SWR). The Next 14/15 single-argument `revalidateTag(tag)` is deprecated in 16.
- `refresh()` — re-render the client's current route only; it does **not** invalidate tagged data, so it is wrong for cached reads.

> Version note: in Next 14/15, the idiomatic call inside an action was `revalidateTag(tag)` / `revalidatePath(path)` (single-argument, immediate expire). Code samples using that form are 14/15-era, not wrong for those versions.

## 2. Why It Matters

- Server Actions are the App Router's default mutation mechanism — you'll use them constantly.
- Their security model is subtle and *dangerous* if misunderstood: they look like local function calls but are **public HTTP endpoints**. This is a favorite senior interview probe because the naive mental model ("it's just a function") leads directly to vulnerabilities.

## 3. The Serialization Boundary

Because arguments travel client→server and results travel back, both must be **serializable** — you cannot pass functions, class instances with methods, or DOM nodes as arguments, and the same limits apply to return values. React's serialization (a superset of JSON: supports Dates, Maps, Sets, promises, FormData, etc.) defines what crosses. This is the same boundary as [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server/Client components]]: data crosses, behavior doesn't.

Practical consequence: pass ids and plain data, not rich objects. A Server Action closing over server-only values (a DB client) is fine — those stay on the server; only its *arguments* and *return* cross the wire.

## 4. The Security Model — Treat Every Action as a Public Endpoint

When you define a Server Action, Next.js creates a stable, callable endpoint reachable by *anyone* — not just your UI. An attacker can invoke it directly with crafted arguments, bypassing your form entirely. Therefore, inside every action you must:

1. **Authenticate** — verify the caller's session/identity ([[20 - Network and Security/04 - Cookies and Auth Patterns|auth]]); never assume "only logged-in users can reach this."
2. **Authorize** — check *this* user may perform *this* operation on *this* resource (the deleteProject action must confirm the user owns the project).
3. **Validate** — the `formData`/arguments are untrusted input; parse with a schema (Zod) — never trust types, which are compile-time only.

```tsx
async function deleteProject(id: string) {
  "use server";
  const session = await auth();
  if (!session) throw new Error("Unauthenticated");                 // authN
  const project = await db.project.findUnique({ where: { id } });
  if (project.ownerId !== session.userId) throw new Error("Forbidden"); // authZ
  await db.project.delete({ where: { id } });
}
```

> [!warning] "It's called from my admin-only page" is not a security control
> The client component that calls an action, and any UI gating around it, is irrelevant to security — the endpoint exists independently and is directly callable. Authorization must live *inside* the action. This is the same lesson as never trusting client-decoded JWT claims ([[20 - Network and Security/04 - Cookies and Auth Patterns|auth]]): the server enforces, the client only presents. Next also protects against CSRF for actions (Origin checks) and uses unguessable action IDs, but that does not replace authN/authZ/validation inside the function.

## 5. Progressive Enhancement

A `<form action={serverAction}>` works **before JavaScript hydrates** (or with JS disabled): Next renders a real form whose submission the framework routes to the action as a native POST, then responds. After hydration, React intercepts the submit and calls the action over fetch without a full navigation — same function, both paths ([[19 - DOM and Browser APIs/08 - Forms and FormData|native form submission]]). This is why knowing native forms matters again: the no-JS path *is* native submission.

Consequence: forms remain functional during slow loads and on flaky connections — a real resilience win you get for free by using form Actions instead of `onClick`+fetch.

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — the "it's just a function" trap:

```tsx
// Called only from an admin dashboard component
async function setUserRole(userId: string, role: string) {
  "use server";
  await db.user.update({ where: { id: userId }, data: { role } });  // ❌ no authN, no authZ, no validation
}
```

Trace the exploit: the action is a public endpoint. Any authenticated (or even unauthenticated, depending on setup) user opens devtools, finds the action call, and replays it with `setUserRole(theirOwnId, "admin")` — privilege escalation to admin, straight past the "admin-only" UI that never ran on their machine. `role` is also unvalidated, so arbitrary strings land in the DB.

Production-safe fix:

```tsx
import { z } from "zod";
const Input = z.object({ userId: z.string().uuid(), role: z.enum(["user", "editor", "admin"]) });

async function setUserRole(raw: unknown) {
  "use server";
  const session = await auth();
  if (session?.role !== "admin") throw new Error("Forbidden");   // authZ: only admins
  const { userId, role } = Input.parse(raw);                     // validate untrusted input
  await db.user.update({ where: { id: userId }, data: { role } });
  updateTag("users");
}
```

Tradeoffs: every action now carries auth + validation boilerplate — extract a `withAuth`/`authorizedAction` wrapper so it's consistent and hard to forget (forgetting is the vulnerability). Schema validation adds a dependency and per-action work but is non-negotiable for a public endpoint. And Server Actions are for *mutations*; using them for reads is an anti-pattern (they're POST-only, uncached, and serialize per call) — read data in Server Components or Route Handlers instead ([[22 - Next.js Deep Dive/05 - Route Handlers and Middleware|Route Handlers]]).

## Real-World Use Cases

### Newsletter signup with `useActionState`: pending, errors, and no-JS support in one

The everywhere-form: email signup in the footer. Server Actions + `useActionState` replace the API route, the fetch wrapper, and the hand-rolled loading/error state:

```tsx
"use client";
import { useActionState } from "react";
import { subscribe } from "./actions";   // "use server" file: validates with Zod, writes, returns state

export function SignupForm() {
  const [state, formAction, pending] = useActionState(subscribe, { error: null });
  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      <button disabled={pending}>{pending ? "Subscribing…" : "Subscribe"}</button>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
```

The action *returns* validation errors as serializable state instead of throwing — that's the data-crosses-the-boundary rule from section 3 put to work. Because it's a real `<form action>`, the pre-hydration submit still works natively (section 5). See [[21 - React Internals and Patterns/10 - React 19|React 19]].

### Optimistic like button: an action called from an event handler

Actions aren't form-only. A social feed's like button should flip instantly and reconcile with the server in the background:

```tsx
"use client";
export function LikeButton({ postId, liked }: { postId: string; liked: boolean }) {
  const [optimisticLiked, setOptimisticLiked] = useOptimistic(liked);
  return (
    <button
      onClick={() =>
        startTransition(async () => {
          setOptimisticLiked(!optimisticLiked);
          await toggleLike(postId);        // Server Action invoked as plain RPC
        })
      }
    >
      {optimisticLiked ? "♥" : "♡"}
    </button>
  );
}
```

Only the serializable `postId` crosses the wire; the action closes over the DB client server-side. If the action rejects, React rolls the optimistic value back to the last server-confirmed state — the reconciliation you'd otherwise hand-write.

### Contact form abuse: rate-limit the endpoint, not the UI

A public contact form's action sends email. Because the action is an open HTTP endpoint, a script can invoke it thousands of times — spam relay and email-provider bills — no matter what the UI throttles:

```tsx
async function sendContactMessage(formData: FormData) {
  "use server";
  const ip = (await headers()).get("x-forwarded-for") ?? "unknown";
  const ok = await rateLimiter.check(`contact:${ip}`, { max: 5, window: "10m" });
  if (!ok) return { error: "Too many messages — try again later." };
  const input = ContactSchema.parse(Object.fromEntries(formData));   // still validate
  await mailer.send(input);
}
```

Same root mechanism as section 4's exploit — the endpoint exists independently of your UI — but the missing control here is abuse throttling, not authZ: even a *correctly validated, unauthenticated-by-design* action needs server-side limits.

> [!tip]
> Fold rate limiting into the same `withAuth`-style wrapper the note recommends, so every action gets validation + auth + throttle by default instead of by memory.

## 7. Interview Answer

Short answer:

> A Server Action is an async `"use server"` function that runs on the server but is callable from the client — Next handles the RPC, so you skip writing an API route and a fetch. Arguments and results must be serializable (data crosses the boundary, not behavior). Crucially, each action is a *public endpoint*, so you must authenticate, authorize, and validate inside it — the calling UI is not a security control.

Deeper answer:

> Used as `<form action>`, they progressively enhance: before hydration the form submits natively as a POST routed to the action; after hydration React calls it over fetch — so forms work without JS. They integrate with React 19 Actions (`useActionState`, `useOptimistic`) for pending/optimistic UI. The security discipline mirrors never trusting client claims: authorization lives in the function, input is validated with a schema since TypeScript types are compile-time only, and actions are for mutations — reads belong in Server Components or Route Handlers. The classic vulnerability is an "admin-only" action with no in-function authZ, directly replayable for privilege escalation.

## 8. Practice

1. <details><summary>Why can't you pass a callback function as an argument to a Server Action?</summary>Arguments cross the client→server boundary and must be serializable; functions carry behavior and closures that can't be serialized and executed on the server as-is. Only data crosses (React's serialization supports JSON plus Dates, Maps, Sets, FormData, promises). Pass serializable data (ids, plain objects); the action itself can close over server-only behavior since that never leaves the server.</details>

2. <details><summary>An action is only called from a component behind an `isAdmin` check. Is it safe without an internal auth check?</summary>No. The action is a public HTTP endpoint with a stable id; anyone can invoke it directly (devtools, curl) regardless of what UI gates it — the client-side `isAdmin` check never runs for an attacker. Authorization must be enforced *inside* the action (verify session + permission on the target resource). UI gating is UX, not security — identical to never trusting client-decoded auth claims.</details>

3. <details><summary>How does a `<form action={serverAction}>` behave with JavaScript disabled, and why is that valuable?</summary>Next renders a real `<form>` that submits natively as a POST; the framework routes it to the Server Action and responds (typically re-rendering/redirecting). So the form works without JS and before hydration completes. Value: resilience — forms stay functional on slow networks, during the hydration gap, and for no-JS clients, which you get automatically by using form Actions instead of onClick+fetch.</details>

4. <details><summary>Why validate `formData` with a schema when your TypeScript types already say `role: "admin" | "user"`?</summary>TypeScript types are erased at compile time — at runtime the action receives whatever bytes the caller sent, which for a public endpoint is attacker-controlled. A malicious client can send `role: "superadmin"` or a non-string; the type annotation does nothing to stop it. Runtime schema validation (Zod `.parse`) is the actual guard, rejecting anything not matching the allowed shape/enum before it reaches the database.</details>

## Related Notes

- [[21 - React Internals and Patterns/10 - React 19|React 19]]
- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[22 - Next.js Deep Dive/05 - Route Handlers and Middleware|Route Handlers and Middleware]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
- [[20 - Network and Security/05 - XSS|XSS]]
- [[01 - Roadmap|Roadmap]]
- [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]] — why action inputs need schema validation, mechanically
- [[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Testing Next.js Boundaries]] — direct-invocation tests with hostile inputs
