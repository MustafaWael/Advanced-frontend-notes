---
tags: [javascript, proxy, reflect, reactivity]
module: "12 - Advanced Language Concepts"
priority: deep-dive
status: not-started
aliases: [Proxy, Reflect, Traps]
---

# Proxy and Reflect

## Maturity Target

- Priority: #deep-dive
- Study time: 45-60 minutes
- Interview signal: you can explain Proxy traps, how Reflect complements them, how Vue/MobX-style reactivity uses proxies, and the performance/invariant costs.
- Production signal: you know when a proxy is the right abstraction (reactivity, validation, virtualization) and when its overhead or invariants make it wrong.
- Dependencies: [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]], [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

## Source Anchors

- [MDN - Proxy](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy)
- [MDN - Reflect](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Reflect)
- [MDN - Proxy handler](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy/Proxy#handler_functions)
- [Vue - Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth.html)

## 1. Concept

A **`Proxy`** wraps a target object and intercepts fundamental operations on it — get, set, has, delete, function call, and more — via **traps** you define in a handler. It lets you customize the *meaning* of ordinary object operations without changing call sites.

**`Reflect`** is a companion object exposing those same fundamental operations as functions (`Reflect.get`, `Reflect.set`, `Reflect.has`, …). Inside a trap, you use Reflect to perform the *default* behavior correctly — including forwarding the `receiver` for proper `this`/getter semantics.

```js
const user = { name: "Ada", age: 36 };

const logged = new Proxy(user, {
  get(target, prop, receiver) {
    console.log("read", prop);
    return Reflect.get(target, prop, receiver);   // default get, receiver forwarded
  },
  set(target, prop, value, receiver) {
    if (prop === "age" && typeof value !== "number") throw new TypeError("age must be a number");
    return Reflect.set(target, prop, value, receiver);
  },
});

logged.name;        // logs "read name" → "Ada"
logged.age = "x";   // throws
```

## 2. Why It Matters

- Proxies power modern reactivity: **Vue 3**, **MobX**, **Valtio**, and Immer-adjacent tools observe reads/writes through proxies to track dependencies and trigger re-renders. Understanding proxies demystifies "how does the framework know my state changed?"
- It's a senior/deep-dive topic that tests whether you understand the object model as something *interceptable*, plus the maturity to weigh its costs.

## 3. How Proxy-Based Reactivity Works

The core idea behind Vue 3 / Valtio: wrap state in a proxy; the `get` trap records "this effect read this property" (dependency tracking), and the `set` trap notifies "this property changed → re-run dependent effects."

```js
// Radically simplified reactive core
let activeEffect = null;
const deps = new WeakMap();

function reactive(obj) {
  return new Proxy(obj, {
    get(t, key, r) {
      if (activeEffect) track(t, key);     // record: current effect depends on t.key
      return Reflect.get(t, key, r);
    },
    set(t, key, value, r) {
      const result = Reflect.set(t, key, value, r);
      trigger(t, key);                      // re-run effects that read t.key
      return result;
    },
  });
}
```

This is why Vue 3 tracks nested property access automatically without `this.setState` — the proxy sees every read and write. It's also why it needed proxies (Vue 2 used `Object.defineProperty`, which couldn't detect added/deleted properties or array index writes — proxies can).

> [!warning] Proxies aren't free, and invariants constrain them
> Every intercepted operation runs your trap function — a real per-access cost versus a plain object, which matters in hot loops over large structures (why reactive libraries are careful about what they wrap and often lazily proxy nested objects). Proxies also must respect *invariants*: e.g., a `get` trap can't return a different value for a non-configurable, non-writable target property, and can't report a non-existent property as absent if the target has it non-configurable — violations throw `TypeError`. This is what `Reflect` + honoring the target is for.

## 4. Reflect and Why the Receiver Matters

`Reflect` methods mirror the traps 1:1, so a trap can delegate to the default correctly. The subtle part is the **receiver** — for getters/setters, the receiver determines what `this` is:

```js
const parent = { get value() { return this._v; }, _v: 1 };
const p = new Proxy(parent, {
  get(t, key, receiver) {
    return Reflect.get(t, key, receiver);   // ✅ getter's `this` is the receiver (proxy/child)
    // return t[key];                        // ❌ getter's `this` would be the raw target
  },
});
```

Forwarding `receiver` keeps inheritance and getter semantics intact when the proxy is used as a prototype or wrapped in another proxy. Omitting it is a subtle correctness bug — the main reason "use `Reflect.get(t, key, receiver)`, not `t[key]`" is the standard trap idiom.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a form library validates fields; the naive version validates only via explicit calls, missing direct assignments.

Buggy version — validation you have to remember to call:

```js
const form = { email: "", age: 0 };
function setField(obj, key, value) {
  validate(key, value);          // only enforced if callers use setField
  obj[key] = value;
}
form.age = -5;                    // ❌ direct assignment bypasses validation entirely
```

Trace: any code path doing `form.key = value` directly skips `setField`, so invalid data slips in — the validation isn't *enforced by the object*, only by discipline.

Production-safe fix — a validating proxy enforces on every write:

```js
function validated(obj, rules) {
  return new Proxy(obj, {
    set(target, key, value, receiver) {
      const rule = rules[key];
      if (rule && !rule(value)) throw new RangeError(`Invalid ${String(key)}: ${value}`);
      return Reflect.set(target, key, value, receiver);
    },
  });
}
const form = validated({ email: "", age: 0 }, {
  age: v => Number.isInteger(v) && v >= 0,
  email: v => /.+@.+/.test(v),
});
form.age = -5;   // throws — validation is now unavoidable, on any assignment path
```

Tradeoffs: the proxy makes validation impossible to bypass (a real robustness win) but adds a trap call to every property write, obscures the object in some debuggers, and can surprise code that does `Object.keys`/spread if you also trap those. Proxies also don't compose transparently with things expecting the raw object (identity checks `proxy === target` are false; some native APIs and `structuredClone` see through or reject them). Alternatives with less magic: explicit setter methods, `Object.defineProperty` accessors, or a schema validated at boundaries ([[20 - Network and Security/07 - Prototype Pollution and Supply-Chain Basics|schema validation]]). Reach for a proxy when you need to intercept *arbitrary, unknown-ahead-of-time* operations uniformly — reactivity, virtualization, sealed/observed objects — not for a couple of known fields.

## 6. Interview Answer

Short answer:

> A Proxy wraps a target and intercepts fundamental operations — get, set, has, delete, apply — through trap functions, so you can redefine what ordinary object operations mean without touching call sites. Reflect exposes those same operations as functions, so inside a trap you call `Reflect.get/set(...)` to perform the correct default behavior, forwarding the receiver for proper getter/`this` semantics.

Deeper answer:

> Proxy-based reactivity (Vue 3, Valtio, MobX) uses the get trap to track which effect read which property and the set trap to trigger dependent effects — which is why these frameworks detect nested reads/writes automatically, and why they moved off `Object.defineProperty` (which missed added/deleted properties and array index writes). Costs: every trapped operation runs your function (hot-path overhead, so libraries proxy lazily), and traps must honor invariants on non-configurable/non-writable properties or throw. Use a proxy when you must intercept arbitrary operations uniformly; for a few known fields, explicit setters or accessors are simpler.

## 7. Practice

1. <details><summary>Why do trap handlers use `Reflect.get(t, key, receiver)` instead of `t[key]`?</summary>`Reflect.get` performs the default get *and* forwards the `receiver`, so if the property is a getter, its `this` is the receiver (the proxy or an object inheriting from it) rather than the raw target. `t[key]` would run the getter with `this` = target, breaking inheritance and any getter that reads other proxied properties. Reflect also mirrors each trap 1:1, making "do the default correctly" explicit and invariant-safe.</details>

2. <details><summary>How does Vue 3 know that `state.user.name = "x"` should re-render, mechanically?</summary>`state` is a reactive proxy; during a component's render, the get trap records that the render effect read `state.user` (and nested access lazily proxies `user`, whose get trap records the read of `name`) — dependency tracking. Assigning `name` fires the set trap on the `user` proxy, which triggers the effects that read `name`, re-running the render. The proxy sees every read/write, so tracking is automatic without explicit setState.</details>

3. <details><summary>Give one reason proxies are avoided in performance-critical code.</summary>Every intercepted operation invokes the trap function instead of a direct native property access, adding function-call and handler-logic overhead per get/set. In hot loops over large data structures this is measurable, which is why reactive libraries proxy lazily (only wrap nested objects when accessed), avoid proxying huge frozen data, and sometimes offer raw/`toRaw` escapes. For a tight numeric loop, a plain object/array is much faster than a proxied one.</details>

4. <details><summary>When is a validating proxy the wrong tool for enforcing constraints on an object?</summary>When the fields and rules are few and known — explicit setter methods, `Object.defineProperty` accessors, or boundary schema validation (Zod) are simpler, faster, and more debuggable, with no per-access overhead or identity/native-API surprises (`proxy !== target`, some APIs see through or reject proxies). A proxy earns its cost when you must intercept *arbitrary, open-ended* operations uniformly — reactivity, observation, virtual objects, access logging — not for validating a handful of properties.</details>

## Related Notes

- [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]
- [[20 - Network and Security/07 - Prototype Pollution and Supply-Chain Basics|Prototype Pollution and Supply-Chain Basics]]
- [[01 - Roadmap|Roadmap]]
