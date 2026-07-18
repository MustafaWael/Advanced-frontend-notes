---
tags: [architecture, react, fsd, clean-architecture, atomic-design]
module: "28 - Frameworks and Application Architecture"
priority: important
status: not-started
aliases: [FSD, Feature-Sliced Design, Clean Architecture frontend, Atomic Design]
---

# Application Architectures

## Maturity Target

- Priority: #important
- Study time: 50 minutes
- Interview signal: Describe FSD, Clean Architecture, and Atomic Design accurately — *and* articulate what each optimizes for, what it costs, and when it's the wrong choice. The "when not" half is the senior signal.
- Production signal: Your folder structure encodes dependency rules, not just file types; a new feature has an obvious home; deleting a feature doesn't leave orphans everywhere.
- Dependencies: [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]], [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]

## Source Anchors

- [Feature-Sliced Design - docs](https://feature-sliced.design/)
- [Uncle Bob - The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Brad Frost - Atomic Design](https://atomicdesign.bradfrost.com/chapter-2/)

## 1. Concept

Simple version: all three are answers to the same question — *where does code go, and what may import what?* — but they slice on different axes: Atomic slices by **visual complexity**, Clean by **distance from I/O**, FSD by **business domain**. The real content of any architecture is its *dependency rule*; folders are just its enforcement surface.

**Atomic Design** (Brad Frost) — a *design-system* taxonomy: atoms (Button) → molecules (SearchField) → organisms (Header) → templates → pages. Strength: shared vocabulary with designers, natural fit for the UI-kit layer. Weakness *as an app architecture*: it classifies by visual granularity, saying nothing about business logic, data, or dependencies — teams burn hours debating "is this a molecule or an organism?" while the actual coupling problem goes unaddressed.

**Clean Architecture** (ported from backend) — concentric layers: entities (domain) ← use-cases (application logic) ← adapters ← frameworks/UI. The **dependency rule**: source dependencies point *inward only*; the domain knows nothing about React or fetch. Strength: framework-independent, highly testable core — right where domain logic is genuinely complex (pricing engines, editors, trading UIs). Weakness: for typical CRUD frontends the "domain" is the backend's; you end up with pass-through use-cases and interface ceremony wrapping what is essentially cache management ([[28 - Frameworks and Application Architecture/06 - Server State|Server State]]).

**Feature-Sliced Design (FSD)** — the frontend-native synthesis. Layers, top → bottom:

```text
app/       providers, router, global config
pages/     route-level composition
widgets/   self-contained page blocks (Header, ProductCard grid)
features/  user interactions with business value (add-to-cart, auth-by-email)
entities/  business nouns (product, user) — their UI + model + api
shared/    UI kit, libs, helpers — zero business knowledge
```

Two rules do the work: (1) **imports point downward only** — a feature may import entities and shared, never another feature, never a page; (2) each *slice* (e.g., `features/add-to-cart`) exposes a **public API** (`index.ts`) — internals are private. Strength: horizontal coupling is structurally banned; features delete cleanly; teams parallelize by slice. Weakness: real ceremony (layer decisions per file), and the feature/entity/widget boundaries are genuinely fuzzy at the edges — teams need conventions docs.

They compose rather than compete: Atomic organizes `shared/ui`; Clean's dependency-inversion thinking governs how `entities` model logic; FSD arranges the app. And the honest default for small apps: **feature folders + shared** ("FSD-lite") — most of the benefit, a fraction of the ceremony.

## 2. Why It Matters

- "How would you structure a large React app?" is a standard senior question — naming an architecture is table stakes; *arguing its costs* is the differentiator.
- The underlying disease is real: type-based folders (`components/`, `hooks/`, `utils/`) scale into cross-import spaghetti where deleting a feature requires an archaeology dig.
- Architecture choices are also *team* choices: FSD's value grows with team size (parallel slices, review boundaries); its ceremony is pure tax on a two-person project.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a 40-dev e-commerce codebase organized by type (`components/`, `hooks/`, `api/`, `utils/`). Two symptoms: (1) removing the "wishlist" feature took a sprint — its pieces were scattered across six folders and imported by cart code; (2) `utils/helpers.ts` is 2,000 lines imported by everything, so every change triggers app-wide review.

Trace: type-based structure has *no dependency rule* — anything imports anything, so coupling grows until every feature transitively touches every other. Nothing enforces feature boundaries because no folder *is* a feature.

```text
Fix: migrate incrementally to FSD
1. Create shared/ and move the genuinely generic (Button, formatDate).
2. Carve entities: entities/product, entities/user (model + api + base UI each).
3. Move each interaction to features/: features/wishlist, features/add-to-cart —
   each with index.ts as its only import surface.
4. Enforce with tooling, not discipline: eslint boundaries rules
   (import/no-restricted-paths or @feature-sliced/eslint-config) fail CI on
   upward/cross-feature imports.
5. Migrate slice-by-slice — FSD tolerates partial adoption; strangle, don't rewrite.
```

Deleting wishlist now = `rm -rf features/wishlist` + fixing the (compiler-listed) page imports.

Tradeoffs: migration is weeks of moves and import rewrites (git blame noise, merge pain — batch it); the team must learn layer semantics and *will* argue widget-vs-feature for months; cross-feature flows (cart needs to know about wishlist promos) force explicit composition at the page/widget layer, which is more code than the sneaky direct import it replaces — that friction is the design working, but it *is* friction.

> [!warning] Footgun: adopting FSD folders without the lint enforcement gives you the ceremony with none of the guarantees — dependency rules that live only in a README decay in one quarter.

## 4. Interview Answer

Short answer:

> The three commonly-named options slice on different axes. Atomic Design classifies UI by visual complexity — atoms to pages — great vocabulary for a design system, but silent on business logic and dependencies. Clean Architecture layers by distance from I/O with dependencies pointing inward — valuable when the frontend owns genuinely complex domain logic, ceremony-heavy for CRUD apps. Feature-Sliced Design is the frontend-native one: layers from app down to shared, slices per business domain, imports only pointing downward, each slice behind a public API. Any of them beats type-based folders, whose real failure is having no dependency rule at all.

Deeper answer:

> The senior addendum is cost-awareness: FSD's boundaries need lint enforcement or they rot; its layer semantics cost onboarding time and are overkill below roughly ten developers — feature-folders-plus-shared captures most value for small teams. Clean's ports-and-adapters earn their keep exactly where domain logic is framework-independent and test-critical, and nowhere else. Atomic belongs inside shared/ui, not as the app's architecture. And they compose: Atomic for the kit, FSD for the app, Clean thinking inside complex entities. The question I'd ask first is team size, domain complexity, and expected lifetime — architecture is a bet on change patterns, not an aesthetic.

## 5. Practice

1. <details><summary>What single mechanism gives FSD its "features delete cleanly" property?</summary>The downward-only import rule plus per-slice public APIs: nothing else may import from inside a feature, and features can't import each other — so a feature's code has no inbound edges except from pages/widgets composing it. Deletion = remove the folder, fix the finite, compiler-visible composition points.</details>
2. <details><summary>Why does Clean Architecture often feel like ceremony in a typical CRUD frontend?</summary>Because the domain logic lives on the backend — the frontend's "use-cases" reduce to fetch-and-display, so entity/use-case/adapter layers wrap what is actually cache management (server state) in pass-through indirection. The pattern pays off only when the client owns real domain rules worth isolating from the framework.</details>
3. <details><summary>Cart needs to show "item also in wishlist." FSD forbids features importing features — what are your options?</summary>Compose at a higher layer: the page/widget queries both features' public APIs and passes data down. Or lower the shared concept: if "wishlist membership" is core, it may belong on the entity layer (entities/product model) both features read. What's not allowed is features/cart importing features/wishlist directly — the coupling would be invisible again.</details>

## Related Notes

- [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]
- [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]
- [[28 - Frameworks and Application Architecture/04 - Meta-Frameworks|Meta-Frameworks]]
- [[24 - Testing and Quality/00 - Testing and Quality MOC|Testing and Quality MOC]]
