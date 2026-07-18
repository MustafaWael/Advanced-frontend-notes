---
tags: [template]
module: "98 - Vault Operations"
priority: important
status: solid
---

# Debugging Incident Template

For real bugs you hit at work (or in a [[90 - Labs/00 - Labs MOC|lab]]). Writing the incident in this shape converts a bad day into interview material and durable knowledge. Copy below the divider; keep it under a page. Save incidents into a `97 - Debugging Incidents/` folder (create it on first use) so they stay separate from curated concept notes.

---

```markdown
---
tags: [debugging-incident, TOPIC-TAG]
module: "97 - Debugging Incidents"
priority: important
status: solid
date: YYYY-MM-DD
---

# INCIDENT TITLE (symptom, not cause: "Search shows results for the previous query")

## Symptom

What was observed, by whom, how often. Exact error text/screenshot reference if any.
Intermittent or deterministic? What made it reproducible (or not)?

## Wrong Turns

What I suspected first and why it was wrong. (This is the part future-you needs.)

## Root Cause

The mechanism, named precisely — link the vault note that owns it:
e.g. a stale closure over the previous render's query ([[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]).

## The Diagnostic That Cracked It

The specific tool/technique that produced the decisive evidence:
breakpoint on X, Network waterfall, Performance profile, git bisect, forced interleaving in a test...

## Fix

​```ts
// The actual change, reduced to its essence
​```

## Tradeoff / Cost of the Fix

What the fix costs or constrains. "None" is almost never true.

## Regression Guard

The test that now pins this behavior ([[24 - Testing and Quality/01 - Testing Mental Model|cheapest layer that catches it]]) — or why one isn't feasible.

## Interview Version (60 seconds, out loud)

Symptom → mechanism → diagnostic → fix → tradeoff. Practice it once.

## Vault Links

- Which existing notes explain this mechanism? Add a backlink there if this is a good real-world example.
- Which note SHOULD have warned me and didn't? Improve it.
```
