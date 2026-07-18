---
tags: [typescript, validation, security, boundaries]
module: "23 - TypeScript Deep Dive"
priority: must-know
status: not-started
aliases: [unknown, runtime validation, Zod]
---

# unknown, Runtime Validation and Boundaries

## Maturity Target

- Priority: #must-know
- Study time: 60 minutes
- Interview signal: explain why types are erased at runtime and how you actually protect an untrusted boundary.
- Production signal: every network response, storage read, env var, and Server Action input passes through one validated parse before typed code touches it.
- Dependencies: [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]], [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]

## Source Anchors

- [TypeScript: unknown](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-0.html#new-unknown-top-type)
- [TypeScript: Narrowing — type predicates](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates)
- [TypeScript: Assertion functions](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#assertion-functions)
- [Zod documentation](https://zod.dev/)
- [MDN: JSON.parse](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse)

## 1. Concept

Types are erased before the code runs ([[23 - TypeScript Deep Dive/01 - Type System Mental Model|mental model]]), so at every point where data *enters* your program, the type system knows nothing. Those entry points are the **untrusted boundaries**:

- HTTP responses (`response.json()` returns `any` — treat it as `unknown`)
- `JSON.parse` of anything (storage, messages, query params)
- `localStorage` / `sessionStorage` reads (users and other tabs can edit them)
- environment variables (`process.env.X` is `string | undefined`, and the string may be garbage)
- form data and Server Action arguments ([[22 - Next.js Deep Dive/04 - Server Actions|public endpoints]])
- `catch (e)` — anything can be thrown, so `e` is `unknown` under `useUnknownInCatchVariables`

`unknown` is the honest type for all of these: it accepts any value but forbids every operation until you produce evidence. `any` is the dishonest one: it accepts any value and permits every operation, letting a wrong assumption travel deep into the app before it explodes.

Evidence comes in three sizes:

```ts
// 1. Built-in narrowing for simple cases
function isString(x: unknown): x is string {          // type predicate
  return typeof x === "string";
}

// 2. Assertion function — throws instead of returning a boolean
function assertPresent<T>(x: T | null | undefined): asserts x is T {
  if (x == null) throw new Error("Expected value to be present");
}

// 3. Schema validation for structured data — the production default
import { z } from "zod";
const Profile = z.object({ id: z.string(), name: z.string(), age: z.number().int().min(0) });
type Profile = z.infer<typeof Profile>;               // single source of truth

const payload: unknown = await response.json();
const profile = Profile.parse(payload);               // throws ZodError on bad shape
```

`z.infer` matters: the schema is the runtime validator *and* the compile-time type, so they cannot drift apart.

## 2. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a settings page persists user preferences to `localStorage` and crashes for a subset of users after a release.

```ts
// Bug: the shape changed between releases, but the cast still claims the old shape.
const prefs = JSON.parse(localStorage.getItem("prefs") ?? "{}") as {
  theme: "light" | "dark";
  fontSize: number;
};
document.body.style.fontSize = `${prefs.fontSize.toFixed(0)}px`; // 💥 fontSize is undefined for old payloads
```

Trace: users who saved prefs under the previous release have `{ theme: "dark" }` stored with no `fontSize`. The `as` cast tells the compiler everything is fine, so nothing warns; the crash happens at `.toFixed()` — far from the boundary that lied.

```ts
// Fix: validate at the boundary, with a fallback for legacy/corrupt data.
const Prefs = z.object({
  theme: z.enum(["light", "dark"]).catch("light"),
  fontSize: z.number().catch(16),
});
const prefs = Prefs.parse(JSON.parse(localStorage.getItem("prefs") ?? "{}"));
```

> [!tip] Parse, don't validate-and-scatter
> Do the parse **once**, at the edge, and let the typed value flow inward. The alternative — sprinkling `if (typeof x.fontSize === "number")` checks wherever data is used — duplicates the boundary everywhere and still misses cases.

Tradeoffs: schemas are code you must maintain, and validating huge payloads has a real (usually small) runtime cost. For hot paths you can validate only the fields you use, or use `safeParse` and degrade gracefully instead of throwing. The cost of *not* validating is crashes far from their cause and, at Server Action boundaries, security holes.

## Real-World Use Cases

### `postMessage` handler in an embeddable widget

A checkout widget runs in an iframe and listens for commands from the host page. Any window can post to it, so `event.data` is the textbook `unknown` — attacker-controlled, not just "maybe stale":

```ts
const HostCommand = z.discriminatedUnion("cmd", [
  z.object({ cmd: z.literal("set_amount"), cents: z.number().int().positive() }),
  z.object({ cmd: z.literal("close") }),
]);

window.addEventListener("message", (event) => {
  if (event.origin !== "https://shop.example.com") return; // authenticate the sender
  const result = HostCommand.safeParse(event.data);         // then validate the payload
  if (!result.success) return;
  handleCommand(result.data);
});
```

`event.data` is typed `any` by the DOM lib, which is exactly the dishonest boundary from section 1 — treat it as `unknown` and parse. `safeParse` fits here because hostile input is *expected* flow, not a bug worth throwing over.

> [!warning]
> Origin check and schema check answer different questions — "who sent this" vs "is it well-formed". Skipping the origin check means any embedded ad or malicious tab can drive your widget with perfectly valid payloads.

### URL search params as shareable state

A product list keeps page, sort, and filters in the URL so views are shareable. Users hand-edit URLs and old bookmarks outlive releases, so `searchParams` is untrusted input in every request:

```ts
const ListParams = z.object({
  page: z.coerce.number().int().min(1).catch(1),
  sort: z.enum(["price_asc", "price_desc", "newest"]).catch("newest"),
});

// /products?page=banana&sort=cheapest → { page: 1, sort: "newest" }
const params = ListParams.parse(Object.fromEntries(searchParams));
```

Everything in a URL is `string | undefined` — `z.coerce` handles the string→number step and `.catch` degrades garbage to defaults instead of rendering a 500 for a mistyped bookmark. Same erased-types reasoning as the localStorage example in section 2, but this boundary is hit on *every* navigation.

### Webhook route handler that returns 400, not 500

A Stripe-style webhook posts payment events to a Route Handler. The sender is a third party whose payload versions change on their schedule, not yours:

```ts
// app/api/webhooks/payments/route.ts
const PaymentEvent = z.object({
  type: z.enum(["payment.succeeded", "payment.failed"]),
  data: z.object({ orderId: z.string(), amountCents: z.number().int() }),
});

export async function POST(req: Request) {
  const parsed = PaymentEvent.safeParse(await req.json());
  if (!parsed.success) {
    return Response.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  await recordPayment(parsed.data); // fully typed from here inward
  return Response.json({ received: true });
}
```

The parse is the single boundary; `recordPayment` and everything behind it never sees `unknown`. A malformed event becomes a logged 400 you can show the provider, instead of a `TypeError` three layers deep in order code ([[22 - Next.js Deep Dive/05 - Route Handlers and Middleware|Route Handlers and Middleware]]).

> [!tip]
> Real webhook endpoints also verify a signature header before parsing — authenticity first, shape second. The same two-step order as the `postMessage` case above.

## 3. Interview Answer

> TypeScript types are erased, so anywhere data enters the program — fetch responses, JSON.parse, localStorage, env vars, form/action inputs, catch variables — the annotations are just hope. I type those entry points as `unknown` and convert them to trusted types through runtime evidence: `typeof`/`in` narrowing for primitives, type predicates or assertion functions for small checks, and a schema library like Zod for structured data, inferring the static type from the schema so validator and type can't drift. `as User` on a response body is the classic anti-pattern: it silences the compiler without testing the data, so the failure surfaces far from the boundary that lied.

## 4. Practice

1. <details><summary>Why is `unknown` preferable to `any` for `catch (e)`?</summary>JavaScript lets you throw anything, so the honest type of a caught value is `unknown`. With `any`, `e.message` compiles even when someone threw a string or `undefined` and crashes at runtime. With `unknown`, you must narrow first — `e instanceof Error ? e.message : String(e)` — which handles every real case. `useUnknownInCatchVariables` (part of `strict`) makes this the default.</details>

2. <details><summary>What's the difference between a type predicate and an assertion function?</summary>A predicate (`x is T`) returns a boolean and narrows in the branch where it's true — the caller decides what to do on failure. An assertion function (`asserts x is T`) throws on failure and narrows all following code. Use predicates when the negative case is expected flow (filtering), assertions when a failure means "this code path should be impossible" and stopping is correct.</details>

3. <details><summary>Your teammate says "we don't need Zod, our backend is TypeScript too, the types are shared." What's wrong?</summary>Shared types guarantee both sides *compile* against the same shape — they do nothing at runtime. The deployed backend may be an older version, a proxy/CDN may alter the payload, the response may be an error body, and for Server Actions the caller may not be your frontend at all. The wire is untrusted regardless of who wrote the other end; validation is about what actually arrives, not what the code intended to send.</details>

4. <details><summary>Where exactly should the parse live for an API call used by five components?</summary>In the single data-access function that performs the fetch (the boundary), not in the components. The function returns a validated, typed value or a typed failure ([[11 - Error Handling/06 - API Error Handling Patterns|error patterns]]); components consume `Profile` and never see `unknown`. One parse point means one place to update when the API changes and no way to "forget" validation in a new call site.</details>

## Related Notes

- [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]]
- [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]
