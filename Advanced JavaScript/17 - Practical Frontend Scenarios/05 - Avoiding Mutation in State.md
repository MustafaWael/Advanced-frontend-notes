---
tags: [javascript, scenarios, react, avoiding-mutation-in-state]
module: "17 - Practical Frontend Scenarios"
priority: must-know
status: not-started
---

# Avoiding Mutation in State

## Maturity Target

- Priority: #must-know
- Study time: 60-80 minutes
- Interview signal: can explain state mutation through reference equality and structural sharing.
- Production signal: can fix stale UI, broken memoization, and accidental shared object updates.
- Fast track: sections 2, 4, 5, and 8.

## Source Anchors

- [React docs: Updating Objects in State](https://react.dev/learn/updating-objects-in-state)
- [React docs: Updating Arrays in State](https://react.dev/learn/updating-arrays-in-state)
- [MDN: Object.is](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is)
- [MDN: Array.prototype.sort](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)

## 1. Scenario

A checkbox toggles data in state, but the UI does not update. Or a memoized child receives the same object reference but its contents changed under the hood.

The cause is usually mutation: existing state was changed in place, then the same reference was passed back to React.

## 2. Broken Version

```tsx
function TaskList() {
  const [tasks, setTasks] = React.useState<Task[]>(initialTasks);

  function toggleTask(id: string) {
    const task = tasks.find(item => item.id === id);
    if (!task) return;

    // BUG: mutates an object inside state.
    task.done = !task.done;

    // BUG: same array reference.
    setTasks(tasks);
  }

  return <TaskTable tasks={tasks} onToggle={toggleTask} />;
}
```

## 3. Root Cause

React compares old and new state by reference with `Object.is`. If you pass back the same array or object, React can treat it as unchanged. Mutation also corrupts the snapshot model: older references now appear to have changed after the fact.

## 4. Fix Arrays

```tsx
function toggleTask(id: string) {
  setTasks(previousTasks =>
    previousTasks.map(task =>
      task.id === id
        ? { ...task, done: !task.done }
        : task
    )
  );
}

function addTask(title: string) {
  setTasks(previousTasks => [
    ...previousTasks,
    { id: crypto.randomUUID(), title, done: false },
  ]);
}

function removeTask(id: string) {
  setTasks(previousTasks =>
    previousTasks.filter(task => task.id !== id)
  );
}

function sortTasks() {
  setTasks(previousTasks =>
    [...previousTasks].sort((a, b) => a.title.localeCompare(b.title))
  );
}
```

Key detail: `sort` mutates, so copy before sorting.

## 5. Fix Nested Objects

```tsx
function updateCity(city: string) {
  setProfile(previous => ({
    ...previous,
    address: {
      ...previous.address,
      city,
    },
  }));
}
```

Copy every object on the path to the changed value. Reuse unchanged branches.

## 6. Fix Map And Set State

```tsx
function selectUser(id: string) {
  setSelectedIds(previous => {
    const next = new Set(previous);
    next.add(id);
    return next;
  });
}

function cacheUser(user: User) {
  setUsersById(previous => {
    const next = new Map(previous);
    next.set(user.id, user);
    return next;
  });
}
```

`Map.prototype.set` and `Set.prototype.add` mutate the collection. Create a new collection first.

## 7. Tradeoffs

- Structural sharing is usually better than deep cloning.
- Deeply nested state may be a sign to normalize by ID or use `useReducer`.
- Immer can reduce boilerplate, but it adds a dependency and hides copying behind proxies.
- TypeScript `readonly` helps catch mutation at compile time but does not freeze runtime objects.

## 8. Production Checklist

- [ ] Did I return a new reference for changed state?
- [ ] Did I avoid mutating nested objects?
- [ ] Did I copy before `sort`, `reverse`, or `splice`?
- [ ] Did I avoid mutating props?
- [ ] Did I keep unchanged branches shared?
- [ ] Would normalized state make this easier?
- [ ] Do memoized children receive stable references when data did not change?

## 9. Interview Angle

Strong answer:

"React state is a snapshot and React uses reference equality. If I mutate an array in place and pass back the same reference, React may skip the render and previous snapshots are corrupted. The fix is structural sharing: create a new array or object for changed containers, copy each nested level on the changed path, and reuse unchanged branches."

## 10. Practice

1. Fix `items.push(item); setItems(items)`.
2. Fix `profile.address.city = city; setProfile(profile)`.
3. Fix `setItems(prev => { prev.sort(...); return prev; })`.
4. Explain when Immer is worth it.

## Related Notes

- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]
