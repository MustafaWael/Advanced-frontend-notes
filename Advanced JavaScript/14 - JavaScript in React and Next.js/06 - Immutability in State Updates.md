---
tags: [javascript, react, nextjs, immutability-in-state-updates]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# Immutability in State Updates

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can explain why mutation breaks React rendering and how structural sharing works.
- Production signal: can update nested objects, arrays, Maps, Sets, and form state without hidden mutation.
- Fast track: sections 3, 5, 6, 8, then write the practice fixes.

## Source Anchors

- [React docs: Updating Objects in State](https://react.dev/learn/updating-objects-in-state)
- [React docs: Updating Arrays in State](https://react.dev/learn/updating-arrays-in-state)
- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [MDN: Object.is](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is)
- [MDN: structuredClone](https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone)
- [MDN: Array.prototype.sort](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)

## 1. Concept

Immutability in React state means you do not modify the existing state object or array. You create a new value that represents the change and pass that new value to the state setter.

React does not freeze JavaScript objects for you. Mutation is allowed by the language, but it breaks React's snapshot and equality assumptions.

```tsx
// Bug: same array reference.
items.push(newItem);
setItems(items);

// Fix: new array reference.
setItems(prev => [...prev, newItem]);
```

## 2. Why It Matters

React uses reference equality to decide whether state changed. If you mutate an object and pass the same reference back, React can skip the render because `Object.is(previousState, nextState)` is `true`.

Mutation also makes debugging harder:

- Old renders can appear to change after the fact.
- Memoized children see same references with changed contents.
- Time-travel debugging and undo stacks become unreliable.
- Concurrent rendering assumptions are weaker when shared objects mutate.
- Tests fail inconsistently because previous fixtures were mutated.

## 3. Official Mechanism

State is a snapshot for a render. Setting state requests a new render with a new snapshot. React expects state updates to replace the changed object or array with a new reference.

Structural sharing is the normal pattern:

- Copy the container that changed.
- Copy each nested object on the path to the changed field.
- Reuse unchanged branches.

```tsx
setProfile(prev => ({
  ...prev,
  address: {
    ...prev.address,
    city: 'Cairo',
  },
}));
```

`profile` is new. `address` is new. Other unchanged nested values can keep their references.

## 4. Mental Model

> [!tip] Mutation changes an object; immutable update changes ownership
> React detects change by comparing references. Producing a *new* object/array (spread, `map`, `filter`, `toSorted`) gives a new identity React can see; mutating in place keeps the old identity and the render is skipped.

Mutation changes an object. Immutable update changes ownership.

| Operation | Mutable version | Immutable version |
| --- | --- | --- |
| Add item | `array.push(item)` | `[...array, item]` |
| Remove item | `array.splice(index, 1)` | `array.filter(...)` |
| Update item | `array[index].done = true` | `array.map(item => item.id === id ? { ...item, done: true } : item)` |
| Sort | `array.sort(...)` | `[...array].sort(...)` |
| Object field | `obj.name = name` | `{ ...obj, name }` |
| Nested field | `obj.a.b = value` | `{ ...obj, a: { ...obj.a, b: value } }` |
| Set | `set.add(value)` | `new Set(set).add(value)` |
| Map | `map.set(key, value)` | `new Map(map).set(key, value)` |

## 5. Real Frontend Example

### Problem: task toggle mutates state

```tsx
type Task = {
  id: string;
  title: string;
  done: boolean;
};

function TaskList() {
  const [tasks, setTasks] = React.useState<Task[]>([
    { id: 'a', title: 'Review PR', done: false },
  ]);

  function toggleTask(id: string) {
    const task = tasks.find(item => item.id === id);
    if (!task) return;

    task.done = !task.done; // BUG: mutates object inside state.
    setTasks(tasks); // Same array reference.
  }

  return <TaskTable tasks={tasks} onToggle={toggleTask} />;
}
```

### Bug

> [!warning] Mutation makes React skip the render
> The object inside the array is mutated, and the same array reference is passed back. React compares by identity, sees the same reference, and can skip the render. Even worse, any previous code holding `tasks` sees the mutated item too.

### Fix

```tsx
function toggleTask(id: string) {
  setTasks(prev =>
    prev.map(task =>
      task.id === id
        ? { ...task, done: !task.done }
        : task
    )
  );
}
```

The fixed code creates a new array and a new object only for the changed task. Unchanged tasks keep their references.

## Real-World Use Cases

### Sorting a React Query cache entry in place

An invoices page sorts the fetched list before rendering. `sort` mutates the array — and that array *is* the cache entry, so every other component reading the same query key now sees the mutated order, and the library's structural sharing breaks.

```tsx
const { data: invoices } = useQuery({ queryKey: ['invoices'], queryFn: fetchInvoices });

// BUG: mutates the shared cache array
const byAmount = invoices?.sort((a, b) => b.amountCents - a.amountCents);

// FIX: sort a copy
const byAmount = invoices?.toSorted((a, b) => b.amountCents - a.amountCents);
```

The cache hands you a reference, not a copy — mutating it changes state you do not own, invisibly to `Object.is` checks.

> [!warning]
> Treat anything you did not create in this render — props, context values, cache results, module constants — as frozen. Mutating them is spooky action at a distance for every other consumer.

### Undo/redo history in a design editor

A canvas editor keeps history as an array of past states. This only works because updates are immutable: each snapshot is a distinct value, and unchanged shapes are structurally shared, so fifty history entries are cheap.

```tsx
function updateShape(id: string, patch: Partial<Shape>) {
  setHistory(prev => {
    const current = prev.present;
    const next = {
      ...current,
      shapes: current.shapes.map(s => (s.id === id ? { ...s, ...patch } : s)),
    };
    return { past: [...prev.past, current], present: next, future: [] };
  });
}
```

Undo is just moving `past[past.length - 1]` back to `present`. If any handler mutated a shape in place, every snapshot sharing that shape's reference would be silently corrupted — history would "rewrite itself."

### Dirty-state check by reference

A settings form enables its Save button only when the draft differs from the last saved snapshot. With immutable updates this is a single reference comparison instead of a deep diff.

```tsx
const isDirty = draft !== savedSnapshot; // O(1), valid only if every edit creates a new object

async function save() {
  await persistSettings(draft);
  setSavedSnapshot(draft); // same reference — isDirty flips to false
}
```

Immutability is what makes change detection this cheap: a new value always has a new identity. One in-place mutation anywhere and `isDirty` stays `false` while the data has changed. See [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]].

## 6. Practical Update Patterns

### Add, remove, update

```tsx
function addTask(title: string) {
  setTasks(prev => [
    ...prev,
    { id: crypto.randomUUID(), title, done: false },
  ]);
}

function removeTask(id: string) {
  setTasks(prev => prev.filter(task => task.id !== id));
}

function renameTask(id: string, title: string) {
  setTasks(prev =>
    prev.map(task =>
      task.id === id ? { ...task, title } : task
    )
  );
}
```

### Sorting without mutation

```tsx
function sortByTitle() {
  setTasks(prev =>
    [...prev].sort((a, b) => a.title.localeCompare(b.title))
  );
}
```

`sort` mutates the array it is called on, so copy first.

### Nested form update

```tsx
type Profile = {
  name: string;
  preferences: {
    theme: 'light' | 'dark';
    email: boolean;
  };
};

function setTheme(theme: Profile['preferences']['theme']) {
  setProfile(prev => ({
    ...prev,
    preferences: {
      ...prev.preferences,
      theme,
    },
  }));
}
```

### Map and Set state

```tsx
function selectId(id: string) {
  setSelectedIds(prev => {
    const next = new Set(prev);
    next.add(id);
    return next;
  });
}

function cacheUser(user: User) {
  setUsersById(prev => {
    const next = new Map(prev);
    next.set(user.id, user);
    return next;
  });
}
```

`Set.prototype.add` and `Map.prototype.set` mutate the collection. Create a new collection first.

## 7. Deep Updates and Alternatives

For deep nested structures, repeated spreading can become noisy. Options:

- Normalize data by ID so updates are shallow.
- Split state into smaller pieces with clearer ownership.
- Use `useReducer` for complex transitions.
- Use Immer when the project already accepts the dependency and the state shape is deeply nested.
- Use `structuredClone` for full deep copies only when you genuinely need to clone broad data before transforming it.

`structuredClone` is not a normal React state-update tool for every change. It can clone many platform data types, but a full deep copy can be expensive and may not preserve class prototypes or functions as you expect.

## 8. Production Tradeoffs

- Prefer targeted structural sharing over full deep cloning.
- Keep state as flat as practical for frequently updated data.
- Use TypeScript `readonly`, `Readonly<T>`, or `ReadonlyArray<T>` to catch accidental mutation at compile time.
- Watch array methods: `push`, `pop`, `shift`, `unshift`, `splice`, `sort`, and `reverse` mutate.
- Modern immutable array methods like `toSorted`, `toReversed`, and `toSpliced` are useful when your runtime support allows them.
- Avoid mutating props. Props are someone else's state.

## 9. Interview Answer

React state should be treated as immutable because React uses reference equality to detect changes and because each render should see a stable snapshot. If I mutate an object or array in place and pass the same reference to the setter, React may bail out and skip the render. The correct pattern is structural sharing: create a new object or array for the part that changed, copy each nested level on the path to the change, and reuse unchanged branches. For complex nested updates, I would consider flattening state, `useReducer`, or Immer, but I would avoid routine deep cloning because it is often wasteful.

## 10. Mistakes to Avoid

| Mistake | Why it fails |
| --- | --- |
| `items.push(item); setItems(items)` | Same array reference; mutation hidden inside existing state. |
| `prev.sort(...)` inside setter | `sort` mutates `prev`; copy before sorting. |
| Shallow copy top level but mutate nested object | Nested reference is still shared. |
| Mutating props for convenience | Parent data is changed from the child, breaking ownership. |
| Deep clone every update | Usually more work than necessary and can hurt performance. |

## 11. Practice

### Q1. Does this rerender?

```tsx
const [user, setUser] = React.useState({ name: 'Mustafa', age: 30 });

function birthday() {
  user.age += 1;
  setUser(user);
}
```

React can skip the render because `user` is the same object reference. Fix:

```tsx
setUser(prev => ({ ...prev, age: prev.age + 1 }));
```

### Q2. Fix the nested tag update.

```tsx
setProfile(prev => ({
  ...prev,
  meta: {
    ...prev.meta,
    tags: [...prev.meta.tags, 'react'],
  },
}));
```

The top-level profile, `meta`, and `tags` references are new. Unchanged fields are structurally shared.

### Q3. Why is this wrong?

```tsx
setItems(prev => {
  prev.reverse();
  return prev;
});
```

`reverse` mutates and returns the same array. Use `setItems(prev => [...prev].reverse())` or `prev.toReversed()` where available.

## Related Notes

- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
- [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]]
