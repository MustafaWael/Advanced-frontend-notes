---
tags: [nextjs, route-handlers, proxy, middleware, nodejs]
module: "22 - Next.js Deep Dive"
priority: important
status: not-started
aliases: [Route Handlers, Proxy, Middleware, Edge Runtime]
verified_on: 2026-07-12
version_scope: "Next.js 14–16"
---

# Route Handlers and Proxy

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can say when to use a Route Handler vs a Server Action, what the current Proxy convention is, and the Node versus legacy Edge constraints.
- Production signal: you put coarse redirects in proxy, build webhooks/public APIs as route handlers, and pick a runtime knowing the tradeoffs.
- Dependencies: [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]], [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]

## Source Anchors

- [Next.js - Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route)
- [Next.js - Proxy](https://nextjs.org/docs/app/api-reference/file-conventions/proxy)
- [Next.js 16 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16)
- [Next.js - Edge and Node.js Runtimes](https://nextjs.org/docs/app/api-reference/edge)
- [MDN - Request](https://developer.mozilla.org/en-US/docs/Web/API/Request)

## 1. Concept

**Route Handlers** (`app/.../route.ts`) are custom HTTP endpoints — the App Router's version of API routes. You export functions named for HTTP methods (`GET`, `POST`, …) that receive a Web `Request` and return a Web `Response`:

```ts
// app/api/webhooks/stripe/route.ts
export async function POST(req: Request) {
  const sig = req.headers.get("stripe-signature");
  const body = await req.text();
  const event = verifyWebhook(body, sig);        // needs the raw body
  await handle(event);
  return new Response(null, { status: 200 });
}
```

**Proxy** (`proxy.ts` at the project root in Next 16) runs before rendering or hitting a route handler. It is for cross-cutting request logic: auth redirects, locale/geo routing, rewrites, header injection, and A/B bucketing. Proxy runs on the **Node.js runtime**, and that runtime cannot be configured. `middleware.ts` is the legacy convention (Next ≤15, where it defaulted to the Edge runtime); in Next 16 it is deprecated and remains only for Edge-runtime use cases until removal. Migration is a rename (`middleware.ts` → `proxy.ts`, exported `middleware` → `proxy`; codemod: `npx @next/codemod@latest rename-middleware-to-proxy .`).

```ts
export function proxy(req: NextRequest) {
  const token = req.cookies.get("session");
  if (!token && req.nextUrl.pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
}
export const config = { matcher: ["/dashboard/:path*"] };
```

## 2. Why It Matters

- Choosing Route Handler vs Server Action vs Server Component for a given need is a common design question, and the wrong choice (e.g., a Route Handler for internal mutations, or heavy logic in middleware) causes real problems.
- Edge vs Node runtime is a senior-level constraint question: pick wrong and your code crashes at deploy (missing Node APIs) or runs slower/costlier than needed.

## 3. When to Use Which

| Need | Use |
| --- | --- |
| Read data for your own pages | Server Component (`await` directly) |
| Mutate data from your own UI | Server Action |
| Public/3rd-party API, webhooks, non-React consumers | Route Handler |
| OAuth callbacks, file downloads, RSS/sitemap, streaming responses | Route Handler |
| Auth gate, redirect, rewrite, geo/locale, headers — before render | Proxy (`proxy.ts`) |

The rule: Server Actions and Server Components are for *your app talking to itself*; Route Handlers are for *the outside world talking to your app* (or when you need raw HTTP control — custom headers, status codes, non-JSON bodies, streaming). Building a Route Handler + client fetch for your own mutations re-introduces the boilerplate Server Actions removed.

## 4. Edge vs Node Runtime

Next code can run on two runtimes:

- **Node.js runtime** (default for route handlers/pages): full Node APIs (`fs`, `crypto`, Buffer, native modules, DB drivers over TCP). Runs in a regular server/serverless function — cold starts, but no capability limits.
- **Edge runtime**: a lightweight V8 environment (Web APIs only — `fetch`, `Request`, Web Crypto) deployed close to users globally. Fast cold starts, low latency, but **no Node APIs, no native modules, no TCP database connections**, and size/CPU limits.

In current Next 16, **Proxy runs on the Node.js runtime**. Older `middleware.ts` deployments are the place you encounter Edge-runtime constraints. Either way, this code runs on every matched request and is in the latency-critical path, so keep it thin.

> [!warning] Common Edge crashes and the middleware trap
> Importing a Node-only library (a Prisma client over TCP, `bcrypt`, anything touching `fs`) into an Edge route or legacy Edge middleware fails at build/deploy or runtime. Current Next 16 Proxy itself runs on Node, but doing a database call or verifying a heavy JWT in proxy on every request still adds latency to every matched request. Keep proxy thin — read a cookie, check a path, redirect — and enforce real authorization at the data layer. For a genuinely Edge runtime route, use HTTP-based drivers designed for it.

## 5. Route Handler Caching Caveat

In Next 15+, `GET` Route Handlers are **not cached by default** (they were in 14) — opt in explicitly if you want caching ([[22 - Next.js Deep Dive/02 - The Caching Layers|caching layers]]). Non-GET handlers are never cached. Under Next 16 Cache Components, GET handlers follow the same prerender model as pages. This is another instance of the [[22 - Next.js Deep Dive/02 - The Caching Layers|default-flip]] confusion — verify per version.

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: protect all `/app/*` routes behind auth, and the team put the check inside each page.

Buggy version — auth scattered across pages:

```tsx
// repeated in every protected page
export default async function DashboardPage() {
  const session = await auth();
  if (!session) redirect("/login");   // duplicated in 40 pages; easy to forget one
  // ...
}
```

Trace the risk: one page missing the check is an auth hole; the logic is duplicated 40 times; and each page still renders partway before redirecting.

Production-safe fix — gate in proxy, keep it thin:

```ts
// proxy.ts (Next 16)
export function proxy(req: NextRequest) {
  const hasSession = req.cookies.has("session");     // cheap cookie presence check only
  if (!hasSession) return NextResponse.redirect(new URL("/login", req.url));
}
export const config = { matcher: ["/app/:path*"] };  // one place, all routes
```

Tradeoffs — and an important nuance: proxy should do a *cheap* check (cookie presence, path matching) and redirect, but it should **not** be your only authorization layer. It is on the request path, so a full DB session validation there raises latency and cost; defense-in-depth means the actual data access (Server Components, Server Actions, Route Handlers) must *also* verify auth ([[22 - Next.js Deep Dive/04 - Server Actions|actions are public endpoints]]) — a forged/expired cookie that passes the presence check must still fail at the data layer. Proxy is the coarse gate and UX redirect; per-resource authorization is enforced where data is touched.

## 7. Interview Answer

Short answer:

> Route Handlers are custom HTTP endpoints (Web Request → Response) for the outside world — public APIs, webhooks, OAuth callbacks, downloads — or when you need raw HTTP control. Server Actions and Server Components handle your app talking to itself. In Next 16, Proxy (`proxy.ts`) runs before a request completes for cross-cutting concerns like auth redirects, rewrites, and locale routing. It is on the request path, so keep it thin.

Deeper answer:

> Edge runtime is Web-APIs-only, globally distributed, fast cold starts, but no Node APIs, native modules, or TCP DB connections; Node runtime has full capability but heavier. In Next 16, `proxy.ts` runs on Node (so the old Edge-compatibility crashes disappear), but it still runs on every matched request, so heavy work (DB calls, bcrypt, full session validation) there is a latency trap — do a cheap cookie/path check and redirect, and enforce real authorization at the data layer for defense in depth. Legacy `middleware.ts` (Next ≤15) defaulted to Edge, which is where the compatibility constraints applied. Also note GET Route Handlers stopped being cached by default in Next 15, another version-flip gotcha.

## 8. Practice

1. <details><summary>You need to accept a Stripe webhook. Route Handler, Server Action, or Server Component — and one detail that trips people up?</summary>Route Handler — it's an external system (Stripe) calling your app over HTTP, not your UI. Server Actions/Components are for your own app. The trip-up: webhook signature verification needs the *raw* request body (`await req.text()`), and you must not let a body parser consume/reshape it first, or the signature check fails. Also return the right status promptly so Stripe doesn't retry.</details>

2. <details><summary>A legacy Edge middleware file imports the Prisma client and deployment fails. Why, and the fix?</summary>An Edge runtime has no Node APIs or TCP sockets, so a standard Prisma client (native engine, TCP DB connection) cannot run there. Fix: keep the boundary thin (check cookie presence / path, redirect) and do full session/DB validation in the Node-runtime data layer (Server Component/Action/Route Handler). In current Next 16, prefer `proxy.ts`, which runs on Node; if you deliberately choose an Edge route, use an HTTP-based/edge-compatible driver.</details>

3. <details><summary>Why is proxy/middleware auth alone insufficient, and what's the defense-in-depth model?</summary>Proxy (Next 16) or legacy middleware does a cheap check (cookie present, path matches) on the request path; it can't affordably do full authorization per resource, and a request could reach data paths through routes the matcher missed. Defense in depth: proxy provides the coarse gate + UX redirect, and every data access point (Server Component, Server Action, Route Handler) independently verifies authentication and authorization on the specific resource. A forged/expired credential passing the presence check must still be rejected where data is read or mutated.</details>

4. <details><summary>When would you deliberately choose the Edge runtime for a route handler despite its limits?</summary>When low global latency and fast cold starts matter more than Node capabilities: geolocation-based redirects, lightweight personalization, A/B assignment, simple auth/token checks with Web Crypto, or streaming responses close to users. The handler must use only Web APIs (fetch, Request, Web Crypto), avoid Node modules and TCP DB drivers (use HTTP-based data access), and stay within size/CPU limits. For heavy computation or Node-dependent work, stay on the Node runtime.</details>

## Related Notes

- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[01 - Roadmap|Roadmap]]
