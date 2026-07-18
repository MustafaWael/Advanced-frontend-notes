---
tags: [javascript, security, prototype-pollution, supply-chain]
module: "20 - Network and Security"
priority: deep-dive
status: not-started
aliases: [Prototype Pollution, Supply Chain]
---

# Prototype Pollution and Supply-Chain Basics

## Maturity Target

- Priority: #deep-dive
- Study time: 45-60 minutes
- Interview signal: you can explain how `__proto__` in attacker JSON corrupts every object, and articulate npm supply-chain risk concretely.
- Production signal: you write merge/clone code that resists prototype pollution and you understand what `npm ci` + lockfiles + provenance actually protect.
- Dependencies: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]], [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]

## Source Anchors

- [MDN - Object prototypes](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Advanced_JavaScript_objects/Object_prototypes)
- [OWASP - Prototype Pollution](https://owasp.org/www-community/attacks/Prototype_Pollution)
- [Snyk - Prototype pollution explained](https://learn.snyk.io/lesson/prototype-pollution/)
- [npm docs - About package provenance](https://docs.npmjs.com/generating-provenance-statements)

## 1. Prototype Pollution — The Mechanism

Almost every object delegates to `Object.prototype` ([[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|the prototype chain]]). If an attacker can write to `Object.prototype`, they inject a property that appears on **every object in the realm** — because failed own-property lookups fall through to the prototype.

The write happens through a bridge from string keys to the prototype: `__proto__` (and `constructor.prototype`). Vulnerable code recursively merges/sets attacker-controlled keys:

```js
function setDeep(obj, path, value) {
  const keys = path.split(".");
  let cur = obj;
  for (let i = 0; i < keys.length - 1; i++) cur = cur[keys[i] ??= {}]; // no key filtering
  cur[keys.at(-1)] = value;
}

setDeep({}, "__proto__.isAdmin", true);   // pollutes Object.prototype
console.log(({}).isAdmin);                 // true  ← every object now "isAdmin"
```

Trace: `obj["__proto__"]` resolves to `Object.prototype`; the final assignment writes `isAdmin` there; subsequently *any* `someObj.isAdmin` check that expected `undefined` reads `true`.

Impact depends on what reads the polluted key: an auth check (`if (user.isAdmin)`), a config default (`options.allowHtml`), a template that concatenates an injected `polluted` property into HTML (→ XSS), or a Node gadget escalating to RCE. Same-shaped bug on server or client.

## 2. Why It Matters

- It's a *language-level* trap that generic "sanitize HTML" advice misses — the sink is object property access, not the DOM.
- It has repeatedly hit foundational libraries (lodash `merge`, jQuery `extend`, deep-set utilities, query-string parsers) — meaning your app can be vulnerable through a transitive dependency you never chose.
- Interviewers use it to see whether you understand prototypes as a *live delegation mechanism*, not just inheritance trivia.

## 3. Defenses

- **Reject dangerous keys** in any code that assigns dynamic string keys: skip `__proto__`, `constructor`, `prototype`.
- **`Object.create(null)`** for maps/dictionaries — no prototype, so no pollution path and no inherited-key collisions. Use a real `Map` when keys are arbitrary ([[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]).
- **`Object.freeze(Object.prototype)`** hardens the realm (measure; some libraries monkeypatch it).
- **Validate input shape** with a schema (Zod/ajv) before merging — untyped `JSON.parse` output is attacker-shaped.
- **`--disable-proto=throw`** (Node flag) and `JSON.parse` reviver stripping `__proto__`.

```js
const FORBIDDEN = new Set(["__proto__", "constructor", "prototype"]);
function safeSetDeep(obj, path, value) {
  const keys = path.split(".");
  if (keys.some((k) => FORBIDDEN.has(k))) throw new Error("unsafe key");
  // ...proceed...
}
```

> [!warning] `{...spread}` and `Object.assign` are safe here; recursive deep-merge is the danger
> Shallow copy doesn't walk into `__proto__` as a data key. The vulnerable pattern is *recursive* deep merge/set that treats every string key as a plain data path. When you must deep-merge untrusted data, use a maintained library version known to filter these keys, or `Object.create(null)` targets.

## 4. Supply-Chain Basics

Your production bundle is mostly *other people's code*: a typical frontend app has hundreds to thousands of transitive npm packages, each an install-time and runtime trust decision. Attack vectors:

- **Malicious/hijacked package**: a maintainer account is compromised or a popular package is sold; a new version exfiltrates env vars or injects a wallet-drainer into the browser bundle (event-stream, ua-parser-js, and others are real precedents).
- **Typosquatting / dependency confusion**: `crossenv` vs `cross-env`, or a public package shadowing a private internal name so the resolver pulls the attacker's.
- **Install scripts**: `postinstall` runs arbitrary code on developer/CI machines — often the real target (secrets, tokens).
- **Compromised build tooling**: the bundler/plugin injects code into every output.

Practical mitigations a senior should name: commit a lockfile and use **`npm ci`** (exact, reproducible installs — no silent range upgrades); pin or narrowly range versions and update deliberately, not automatically; run `npm audit`/Snyk/Dependabot but triage (reachability matters — a vuln in an unused code path is lower priority); minimize dependency count (every `npm install` is a trust extension — do you need a package for `is-odd`?); disable install scripts where feasible (`--ignore-scripts` + allowlist); prefer packages with **provenance**/signed publishing and healthy maintenance; and use Subresource Integrity (`integrity` hashes) for any script loaded from a CDN so a compromised CDN can't swap the file.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dashboard merges server-provided user preferences over defaults with an old deep-merge util.

Buggy version:

```js
import merge from "some-deep-merge@vulnerable";
const config = merge({ theme: "light", allowHtmlBio: false }, await fetchUserPrefs());
if (config.allowHtmlBio) renderRawHtml(bio);   // gated feature
```

Trace: attacker sets their prefs (or a MITM alters the response) to include `{"__proto__": {"allowHtmlBio": true}}`. The vulnerable merge writes `allowHtmlBio: true` onto `Object.prototype`. Now the gate reads `true` — not just for the attacker but for *every* config object in the app — unlocking raw-HTML rendering → chained XSS ([[20 - Network and Security/05 - XSS|XSS]]).

Production-safe fix:

```js
import { z } from "zod";
const Prefs = z.object({ theme: z.enum(["light", "dark"]).optional() }).strict(); // unknown keys rejected

const prefs = Prefs.parse(await fetchUserPrefs());   // __proto__ / extra keys thrown out
const config = { theme: "light", allowHtmlBio: false, ...prefs }; // shallow, schema-validated
```

Tradeoffs: schema validation adds a dependency and upfront work per endpoint, and `.strict()` means adding a legitimate pref requires a schema change (a feature, not a bug, for untrusted input). Using `Object.create(null)` targets or a patched merge library is lighter but doesn't give you the type/shape guarantees — the belt-and-suspenders answer is validate at the boundary *and* keep merge utilities current.

## 6. Interview Answer

Short answer:

> Prototype pollution is writing to `Object.prototype` via keys like `__proto__` in attacker-controlled data, usually through a recursive deep-merge/set that trusts every string key. Because objects delegate to the prototype, the injected property appears on every object — corrupting auth checks, config gates, or templates. Defenses: reject `__proto__`/`constructor`/`prototype` keys, use `Object.create(null)` or `Map`, and validate input shape with a schema.

Deeper answer:

> Supply chain is the broader version of "you run code you didn't write": hundreds of transitive npm packages, each a trust decision, exposed to hijacked releases, typosquatting, dependency confusion, and malicious install scripts. Mitigations are lockfiles with `npm ci`, deliberate updates, audited and provenance-signed dependencies, minimizing dependency count, controlling install scripts, and SRI for CDN scripts. Both topics reduce to the same principle: untrusted input — whether a JSON body or a package — must be constrained at the boundary.

## 7. Practice

1. <details><summary>Why does `const m = {}; m["__proto__"]["polluted"] = 1` affect unrelated objects, but `const m = Object.create(null); m["__proto__"] = {...}` does not?</summary>In the first, `m["__proto__"]` is the accessor that returns `Object.prototype`; writing to it mutates the shared prototype every object inherits from → global effect. `Object.create(null)` has no prototype and no `__proto__` accessor, so `m["__proto__"]` is just an ordinary own data key — the write stays local and pollutes nothing.</details>

2. <details><summary>Which are exploitable: `Object.assign(target, userInput)`, `{...userInput}`, a recursive `deepMerge(target, userInput)`?</summary>The recursive `deepMerge` is the classic vulnerable one — it walks into nested keys and can follow `__proto__` into the prototype. `Object.assign` and spread copy own enumerable properties shallowly and treat `__proto__` in a source object as a normal own key on the *target* (not a prototype write in the typical case), so they're not the pollution vector. The danger is specifically recursion + unfiltered string keys.</details>

3. <details><summary>A teammate wants to auto-merge Dependabot minor/patch PRs to "stay secure." Argue both sides.</summary>For: reduces window of known-vuln exposure, less manual toil, patches often are safe. Against: auto-merging *is itself* a supply-chain risk — a compromised patch release lands in production with no human review (this is a real attack path); semver is a promise maintainers sometimes break. Senior stance: auto-merge is acceptable only with strong gates — passing tests, provenance/signature verification, a soak/delay window, and lockfile + `npm ci`. Fully unattended auto-merge trades one risk for another.</details>

4. <details><summary>How does Subresource Integrity defend a `<script src="https://cdn.example/lib.js">`, and what's its limitation?</summary>The `integrity="sha384-…"` attribute makes the browser hash the fetched file and refuse to execute it if the hash doesn't match — so a compromised or swapped CDN file is blocked. Limitation: it protects a *pinned* file, not versioned/mutable URLs or dynamically loaded chunks, and you must update the hash on every legitimate change. It guards CDN integrity, not a maliciously published npm package that's bundled at build time.</details>

## Related Notes

- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[20 - Network and Security/05 - XSS|XSS]]
- [[01 - Roadmap|Roadmap]]
