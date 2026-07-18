---
tags: [javascript, react, nextjs, server-vs-client-javascript-in-nextjs]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
aliases: [RSC, Server Components]
---

# Server vs Client JavaScript in Next.js

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: can explain Server Components, Client Components, `'use client'`, hydration, and serializable props.
- Production signal: can place JavaScript in the right runtime to reduce bundle size, protect secrets, and avoid hydration bugs.
- Fast track: sections 3, 5, 6, 8, and practice Q1-Q5.

## Source Anchors

- [Next.js docs: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [Next.js docs: Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data)
- [Next.js docs: App Router glossary](https://nextjs.org/docs/app/glossary)
- [React docs: Server Components](https://react.dev/reference/rsc/server-components)
- [React docs: 'use client'](https://react.dev/reference/rsc/use-client)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

In the Next.js App Router, components are Server Components by default. Server Components run on the server and do not add their component code to the client JavaScript bundle. Client Components are marked by a `'use client'` directive at the top of a module. They can use state, effects, event handlers, refs, and browser APIs.

The key is that "server" and "client" are not just deployment labels. They define which JavaScript APIs exist, where code is bundled, how data crosses boundaries, and when hydration happens.

## 2. Why It Matters

Correct runtime placement affects:

- Bundle size: unnecessary `'use client'` high in the tree pulls more code into the browser bundle.
- Security: server-only secrets, database clients, and private tokens must not reach the browser.
- UX: server-rendered HTML can show content faster, while client components provide interactivity.
- Hydration correctness: initial server and client output must match for hydrated client components.
- Data ownership: server data fetching can reduce client waterfalls and duplicated loading states.

## 3. Official Mechanism

### Server Components

Server Components:

- Are the default in the App Router.
- Render on the server.
- Can be `async`.
- Can fetch data close to the source.
- Can use server-only resources such as database clients or private environment variables.
- Cannot use React state, effects, event handlers, or browser APIs.
- Do not ship their component implementation to the browser bundle.

```tsx
// app/products/page.tsx
// Server Component by default.
import { db } from '@/lib/db';
import ProductList from './ProductList';

export default async function ProductsPage() {
  const products = await db.product.findMany();

  return <ProductList products={products} />;
}
```

### Client Components

Client Components:

- Are marked with `'use client'` at the top of a file.
- Can use `useState`, `useEffect`, event handlers, refs, and browser APIs.
- Are prerendered into HTML on the first load, then hydrated in the browser.
- Render entirely on the client on subsequent client-side navigations.
- Add their module graph to the client JavaScript bundle.

```tsx
// app/products/AddToCartButton.tsx
'use client';

import * as React from 'react';

export default function AddToCartButton({ productId }: { productId: string }) {
  const [pending, setPending] = React.useState(false);

  return (
    <button
      disabled={pending}
      onClick={async () => {
        setPending(true);
        await addToCart(productId);
        setPending(false);
      }}
    >
      Add to cart
    </button>
  );
}
```

## 4. Mental Model

Think in module graphs:

- A Server Component can import other Server Components and Client Components.
- A module with `'use client'` creates a client boundary.
- Everything imported by that client module becomes part of the client module graph.
- Server Components can pass serializable props to Client Components.
- Client Components cannot directly import Server Components as normal child modules, but Server Components can pass server-rendered UI as `children` or props where supported.

> [!tip] Push the client boundary as low as practical
> Keep static layout, data fetching, markdown rendering, database access, and secret-bearing code on the server. Move only interactive islands to the client — everything imported by a `'use client'` module joins the client bundle.

## 5. Real Frontend Example

### Problem: layout marked as client

```tsx
// app/layout.tsx
'use client';

import SearchBox from './SearchBox';
import Logo from './Logo';
import MarketingNav from './MarketingNav';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav>
        <Logo />
        <MarketingNav />
        <SearchBox />
      </nav>
      {children}
    </>
  );
}
```

### Bug

> [!warning] `'use client'` at the top pulls everything client-side
> The whole layout module graph becomes client-side. Static components like `Logo` and `MarketingNav` get bundled for the browser even though only `SearchBox` needs interactivity — shipping JS the user never needed.

### Fix: move `'use client'` down

```tsx
// app/layout.tsx
import Logo from './Logo';
import MarketingNav from './MarketingNav';
import SearchBox from './SearchBox';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav>
        <Logo />
        <MarketingNav />
        <SearchBox />
      </nav>
      {children}
    </>
  );
}
```

```tsx
// app/SearchBox.tsx
'use client';

import * as React from 'react';

export default function SearchBox() {
  const [query, setQuery] = React.useState('');

  return (
    <input
      value={query}
      onChange={event => setQuery(event.target.value)}
      placeholder="Search"
    />
  );
}
```

Only the interactive search box needs client JavaScript.

## Real-World Use Cases

### A secret that must never join the client graph

A billing module holds the Stripe secret key. One careless import from a `'use client'` file — even three levels deep — would bundle it for the browser. The `server-only` package turns that mistake into a build error.

```ts
// lib/billing.ts
import 'server-only';
import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
```

This works because `'use client'` marks a module-graph boundary: everything a client module imports gets bundled, so the leak happens at import time, not call time — which is exactly where `server-only` throws.

> [!tip]
> Mirror it with `import 'client-only'` in modules that touch `window`, so a Server Component cannot accidentally import them either.

### Markdown rendering that ships zero JavaScript

A blog renders MDX with syntax highlighting. Shiki plus the markdown pipeline is well over a megabyte of JavaScript — in a Server Component it runs at request/build time and the browser receives only HTML.

```tsx
// app/blog/[slug]/page.tsx — Server Component by default
import { renderMarkdown } from '@/lib/markdown'; // pulls in shiki — server-only cost

export default async function PostPage({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);
  const html = await renderMarkdown(post.body);

  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}
```

Server Components do not ship their implementation or their dependencies to the client bundle — heavy transform libraries are the biggest single win of that rule. See [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]].

### Server content inside an interactive shell via `children`

Legal terms are static server-rendered content, but the accordion around them needs state. A Client Component cannot *import* a Server Component — but it can receive already-rendered server UI as `children`.

```tsx
// page.tsx — Server Component
<CollapsibleSection title="Terms of Service">
  <LegalText /> {/* stays a Server Component: rendered on the server, passed as children */}
</CollapsibleSection>
```

```tsx
// CollapsibleSection.tsx
'use client';

export default function CollapsibleSection({ title, children }: Props) {
  const [open, setOpen] = React.useState(false);

  return (
    <section>
      <button onClick={() => setOpen(prev => !prev)}>{title}</button>
      {open && children}
    </section>
  );
}
```

The boundary is about the module graph, not the render tree: the server renders `LegalText` and passes the result through the client "hole," so interactivity wraps server content without pulling it into the bundle.

## 6. Data Passing and Serialization

Server Components can pass props to Client Components, but those props need to be serializable by React.

```tsx
// Server Component
export default async function Page() {
  const product = await getProduct();

  return (
    <AddToCartButton
      productId={product.id}
      priceCents={product.priceCents}
    />
  );
}
```

Avoid passing:

- functions, unless they are supported server functions/actions in the relevant context
- database clients
- class instances with behavior
- non-serializable browser objects
- secrets

Prefer passing plain data and IDs. If a Client Component needs to trigger server work, use a Server Action, route handler, or API endpoint depending on the app architecture.

## 7. Browser APIs and Effects

Server Components cannot read browser APIs:

```tsx
// BUG in a Server Component.
const width = window.innerWidth;
```

Move browser-only reads into a Client Component effect:

```tsx
'use client';

function WindowWidth() {
  const [width, setWidth] = React.useState<number | null>(null);

  React.useEffect(() => {
    function update() {
      setWidth(window.innerWidth);
    }

    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return <span>{width === null ? 'Loading' : `${width}px`}</span>;
}
```

The first render is server-safe. The browser-specific value is read after hydration.

## 8. Decision Table

| Requirement | Prefer |
| --- | --- |
| Fetch from database or use private token | Server Component, route handler, or Server Action |
| Render static content or layout | Server Component |
| Use `useState`, `useEffect`, refs, browser events | Client Component |
| Read `window`, `document`, `localStorage`, media queries | Client Component effect |
| Add an interactive button, dropdown, modal, search input | Small Client Component island |
| Pass data from server to interactive UI | Serializable props |
| Handle a mutation | Server Action or API route plus client UI |
| Use a browser-only library | Client Component, sometimes dynamic import with SSR disabled |

## 9. Production Tradeoffs

- Put `'use client'` at the leaf, not the root, unless the whole subtree truly needs interactivity.
- Keep server-only modules out of client graphs. Watch imports carefully.
- Passing large data to Client Components increases HTML/RSC payload and client memory pressure.
- Server fetching improves security and can reduce waterfalls, but interactive live data may still belong to a client data library.
- Client Components are not bad. They are the correct tool for browser interaction.
- Hydration means Client Components need deterministic initial output if they are prerendered.

## 10. Interview Answer

In the Next.js App Router, components are Server Components by default. They run on the server, can be async, can fetch data and access server-only resources, and do not ship their component code to the browser. A file with `'use client'` creates a Client Component boundary. Client Components can use hooks, event handlers, refs, and browser APIs, and they are hydrated in the browser. The boundary also affects bundling: imports under a client module become part of the client graph. Data passed from Server Components to Client Components must be serializable by React, so I pass plain data or IDs and keep secrets and database clients on the server.

## 11. Mistakes to Avoid

| Mistake | Why it hurts |
| --- | --- |
| Marking `layout.tsx` with `'use client'` for one small interaction | Pulls too much UI into the client bundle. |
| Importing server-only code into a client file | Can leak secrets or fail the build/runtime. |
| Reading `window` during render | Breaks on the server or causes hydration mismatch. |
| Passing functions/classes as ordinary client props | Props must be serializable by React. |
| Assuming Client Component means "only browser" | First load can be prerendered to HTML and then hydrated. |

## 12. Practice

### Q1. Where does this belong?

```tsx
const rows = await db.invoice.findMany();
```

Server Component, route handler, or Server Action. It should not be in a Client Component because it uses server-only database access.

### Q2. Where does this belong?

```tsx
const [open, setOpen] = React.useState(false);
```

Client Component. State and event-driven interactivity require a client boundary.

### Q3. What is wrong with this prop?

```tsx
<ClientWidget onSave={() => saveToDatabase()} />
```

An ordinary function is not a serializable prop from a Server Component to a Client Component. Use a Server Action where appropriate, or expose an API/route handler and call it from the client.

### Q4. Why is `'use client'` high in the tree expensive?

It moves the marked module and its imports into the client module graph. That can increase browser JavaScript, parse time, memory, and hydration work.

### Q5. Is a Client Component always bad for performance?

No. It is necessary for interactivity. The mature decision is to keep client islands focused and avoid turning static or server-data-heavy UI into client code unnecessarily.

## Related Notes

- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]
- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]
- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[01 - Roadmap|Roadmap]]
