---
name: add-use-cases
description: Enrich a concept note in the Advanced JavaScript Obsidian vault with a "Real-World Use Cases" section — 2-4 concrete production scenarios with runnable code. Use this whenever the user asks for use cases, examples, real-world applications, "where would I use this", "when does this matter", or asks to make a note (or module) more practical/applied — even if they don't say "use cases" explicitly. Also use when reviewing notes for practical depth.
---

# Add Real-World Use Cases

Enrich vault concept notes with production use cases. The vault's owner is a mid-level React/Next.js developer preparing for interviews; the vault's maturity bar says a topic is only learned when you can connect it to real production work. Many notes explain the mechanism well but show only one bug→fix example — this skill adds breadth: the several distinct places the concept actually shows up in a working frontend codebase.

## Workflow

1. **Locate the note.** If the user names a concept, find its note in the vault (folder names are numbered modules, e.g. `03 - Scope and Variables/05 - Closures.md`). If they name a module, list its notes and process the ones they pick (or all, if asked).
2. **Read the whole note first.** Understand which examples already exist — especially section "3. Real Frontend Example: Bug → Fix → Tradeoff". Your use cases must NOT duplicate it. If a note already has a Real-World Use Cases section, improve/extend it rather than adding a second one.
3. **Generate 2-4 use cases** (see quality bar below).
4. **Insert the section** into the note (see placement rules).
5. **Summarize** in one or two lines per note what you added.

## Quality bar for a use case

Each use case earns its place only if a working developer would nod at it. For each one provide:

- **A scenario title** naming a real feature or system: "Debounced search input", "Auth token refresh queue", "Infinite scroll with IntersectionObserver" — not "Example 1".
- **The situation**: 1-2 sentences on the product context and why this concept is the load-bearing piece.
- **A short runnable code example** (modern JS/TS, React/Next.js where natural, 5-20 lines). Realistic identifiers, no `foo`/`bar`. Trim boilerplate that doesn't teach.
- **The connection**: one sentence naming the exact mechanism from the note that makes the example work or fail.
- Where a footgun exists, add a `> [!warning]` callout; where there's a production pattern worth stealing, `> [!tip]`. Only where they earn their place.

Aim for diversity across the 2-4 cases: different layers (UI event handling, data fetching, state management, tooling/build, Node/server) rather than four variations of the same trick. At least one should be a scenario plausible in the user's daily React/Next.js work.

Avoid: contrived counter/todo-list examples (unless the concept genuinely is about state primitives), restating the note's existing Bug→Fix example, and encyclopedic lists without code.

### The classic interview example

Most core concepts have one canonical snippet interviewers reach for — for closures it's `setTimeout` inside a `for` loop with `var` vs `let`; for `this` it's a detached method call; for the event loop it's the promise-vs-setTimeout ordering question. These matter because the user WILL be asked them, and because they knot several mechanisms together (the closures classic touches per-iteration bindings, `var` hoisting, and event loop timing at once).

Check whether the note already covers its classic. If it doesn't, add it as the first use case, titled "Classic interview trap: ..." — with the snippet, the wrong-guess output, a **tick-by-tick trace** of why (name each mechanism: binding creation, task queue, etc.), the `let`/modern fix, and wikilinks to the sibling concepts involved (e.g. [[03 - Scope and Variables/03 - var let const|var let const]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]). If the note covers it but only shallowly (code without trace), deepen it in place instead of duplicating.

## Placement and vault conventions

- Insert a `## Real-World Use Cases` section **after** section "3. Real Frontend Example" (or after "2. Why It Matters" if 3 is absent), and always **before** "## 4. Interview Answer" if renumbering can be avoided — otherwise place it directly **before** "## Related Notes". Never renumber existing sections; keep the new section unnumbered.
- Wikilinks use full path + alias: `[[19 - DOM and Browser APIs/06 - Observers|Observers]]`. Link each use case to the other vault notes it touches — cross-links are how the vault compounds.
- Never modify frontmatter except: do not touch `status` at all (it's the learner's progress marker).
- Callout syntax: `> [!warning]` and `> [!tip]`.
- Keep the note's voice: direct, mechanism-first, no filler.

## Example shape

```markdown
## Real-World Use Cases

### Stale closure in a polling hook

A dashboard polls an endpoint every 10s. The interval callback closes over the first render's `filters`, so the poll silently ignores every filter change.

​```tsx
useEffect(() => {
  const id = setInterval(() => fetchOrders(filters), 10_000); // `filters` frozen at mount
  return () => clearInterval(id);
}, []); // missing dep — the closure never updates
​```

Works/fails because closures capture **bindings from the creation-time environment** — the effect ran once, so its environment is frozen.

> [!warning]
> Adding `filters` to the deps fixes staleness but resets the interval on every change — decide which behavior the product needs.

See [[14 - JavaScript in React and Next.js/03 - Stale Closures in Hooks|Stale Closures in Hooks]].
```

## When invoked on chat questions (no note editing)

If the user just asks "give me use cases for X" without wanting the vault touched, produce the same quality of output in chat and offer to save it into the note.
