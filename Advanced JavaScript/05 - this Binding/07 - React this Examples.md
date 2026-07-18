---
tags: [javascript, this-binding, react-this-examples, react]
module: "05 - this Binding"
priority: important
status: not-started
---

# React this Examples

## Maturity Target

- Priority: #important
- Study time: 75-90 minutes
- Interview signal: you can explain why class component methods lose `this` and how hooks changed the problem.
- Production signal: you can maintain class components safely and avoid translating class `this` mental models into hooks incorrectly.
- Dependencies: [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]], [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]], [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]

## Source Anchors

- [React - Component](https://react.dev/reference/react/Component)
- [React - State: a component's memory](https://react.dev/learn/state-a-components-memory)
- [React - Responding to events](https://react.dev/learn/responding-to-events)
- [MDN - this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN - Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions)

## 1. Concept

React class components use JavaScript classes. Their methods are not automatically bound to the instance.

```jsx
class Counter extends React.Component {
  state = { count: 0 };

  increment() {
    this.setState((state) => ({ count: state.count + 1 }));
  }

  render() {
    return <button onClick={this.increment}>{this.state.count}</button>;
  }
}
```

Bug: `onClick={this.increment}` passes the function value. When React calls it later, it is not called as `instance.increment()`, so `this` is `undefined` inside `increment`.

Function components do not have component instance `this`.

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount((current) => current + 1)}>
      {count}
    </button>
  );
}
```

Hooks moved most modern React code away from `this`, but class components still appear in legacy code, error boundaries, and interviews.

## 2. Why It Matters

You need this topic for:

- Maintaining older React codebases.
- Debugging `Cannot read properties of undefined` inside class handlers.
- Understanding constructor binding vs arrow fields.
- Migrating class components to hooks.
- Explaining why hooks use closures instead of `this`.
- Recognizing that stale closures in hooks are a different problem from class `this`.

## 3. Bug: Unbound Class Method

```jsx
class SaveButton extends React.Component {
  state = { saving: false };

  async handleClick() {
    this.setState({ saving: true });
    await this.props.onSave();
    this.setState({ saving: false });
  }

  render() {
    return (
      <button onClick={this.handleClick}>
        {this.state.saving ? "Saving..." : "Save"}
      </button>
    );
  }
}
```

> [!warning] Failure mode
> clicking throws because `this` is `undefined` inside `handleClick`.

Why: passing `this.handleClick` to React passes the method function. It does not preserve the receiver.

## 4. Fix 1: Bind in Constructor

```jsx
class SaveButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = { saving: false };
    this.handleClick = this.handleClick.bind(this);
  }

  async handleClick() {
    this.setState({ saving: true });
    await this.props.onSave();
    this.setState({ saving: false });
  }

  render() {
    return (
      <button onClick={this.handleClick}>
        {this.state.saving ? "Saving..." : "Save"}
      </button>
    );
  }
}
```

Tradeoff:

- One bound function per instance.
- Stable identity across renders.
- Clear for older React codebases.

## 5. Fix 2: Arrow Class Field

```jsx
class SaveButton extends React.Component {
  state = { saving: false };

  handleClick = async () => {
    this.setState({ saving: true });
    await this.props.onSave();
    this.setState({ saving: false });
  };

  render() {
    return (
      <button onClick={this.handleClick}>
        {this.state.saving ? "Saving..." : "Save"}
      </button>
    );
  }
}
```

Why it works: the arrow field is created for the instance and captures instance `this`.

Tradeoff:

- Very convenient.
- One function per instance.
- Not a prototype method, which can matter for inheritance and testing patterns.

## 6. Fix 3: Arrow Wrapper in Render

```jsx
class SaveButton extends React.Component {
  state = { saving: false };

  async handleClick() {
    this.setState({ saving: true });
    await this.props.onSave();
    this.setState({ saving: false });
  }

  render() {
    return (
      <button onClick={() => this.handleClick()}>
        {this.state.saving ? "Saving..." : "Save"}
      </button>
    );
  }
}
```

Tradeoff:

- Easy for passing arguments.
- Creates a new function every render.
- Usually fine for small components.
- Can hurt memoized children or unnecessary re-renders if passed deep.

Use it intentionally, not as a reflex.

## 7. Passing Arguments

Constructor-bound method:

```jsx
class ProductList extends React.Component {
  constructor(props) {
    super(props);
    this.selectProduct = this.selectProduct.bind(this);
  }

  selectProduct(productId) {
    this.props.onSelect(productId);
  }

  render() {
    return this.props.products.map((product) => (
      <button
        key={product.id}
        onClick={() => this.selectProduct(product.id)}
      >
        {product.name}
      </button>
    ));
  }
}
```

The inline wrapper is used to provide `product.id`, not to fix `this` because the method is already bound.

## 8. Hooks: No Instance `this`

Function components use closures, props, state, and refs.

```jsx
function SaveButton({ onSave }) {
  const [saving, setSaving] = useState(false);

  async function handleClick() {
    setSaving(true);
    await onSave();
    setSaving(false);
  }

  return (
    <button onClick={handleClick}>
      {saving ? "Saving..." : "Save"}
    </button>
  );
}
```

No `this` is involved. The main bug class shifts from context loss to stale closures, dependency arrays, async cleanup, and referential equality.

## 9. Class to Hook Migration Mental Model

Class:

```jsx
class Timer extends React.Component {
  state = { count: 0 };

  componentDidMount() {
    this.id = setInterval(() => {
      this.setState((state) => ({ count: state.count + 1 }));
    }, 1000);
  }

  componentWillUnmount() {
    clearInterval(this.id);
  }
}
```

Function component:

```jsx
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount((current) => current + 1);
    }, 1000);

    return () => clearInterval(id);
  }, []);

  return <p>{count}</p>;
}
```

Class instance fields like `this.id` become local effect-owned values, refs, or state depending on whether they affect rendering.

## 10. Real Production Checklist

- Is this a class component or function component?
- Is a class method passed as a callback?
- Is the method bound once in the constructor or defined as an arrow field?
- Is `.bind(this)` being called inside `render` repeatedly?
- Is an inline arrow being passed to a memoized child?
- Is a class instance field being migrated to `useRef`, `useState`, or local effect variable correctly?
- Is a hook callback bug actually stale closure, not `this`?
- Is an error boundary still class-based? If yes, class `this` still matters.

## 11. Interview Answer

Short answer:

> React class component methods are not automatically bound. If you pass `this.handleClick` as a callback, it can lose `this`. Fix it by binding in the constructor, using an arrow class field, or wrapping the call in an arrow.

Deeper answer:

> Class methods live on the prototype and follow normal JavaScript `this` rules. `onClick={this.handleClick}` passes a function reference, not a method call with a receiver. Constructor binding creates a stable bound function per instance; arrow class fields capture instance `this`; inline arrows create a new function during render.

Production answer:

> In modern function components, there is no component instance `this`. The equivalent mental model is closures over render values, plus refs for mutable instance-like data. Do not confuse class `this` bugs with hook stale closure bugs.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "React binds class methods automatically." | It does not. |
| "Hooks use `this` under the hood." | Function components use closures and React-managed state. |
| "Inline arrows in render are always bad." | They are often fine; identity matters in specific memoized paths. |
| "Arrow class fields are prototype methods." | They are per-instance properties. |
| "Class instance fields map directly to state in hooks." | Some map to refs or effect locals instead. |

## 13. Practice

1. Fix this class component three ways:

```jsx
class Counter extends React.Component {
  state = { count: 0 };

  increment() {
    this.setState((state) => ({ count: state.count + 1 }));
  }

  render() {
    return <button onClick={this.increment}>{this.state.count}</button>;
  }
}
```

2. Explain the tradeoff between constructor binding and arrow class fields.
3. Convert a class interval using `this.id` into a hook using an effect cleanup.
4. Identify whether a bug is context loss or stale closure.
5. Explain why error boundaries keep class `this` relevant in React codebases.

## Related Notes

- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]
- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[01 - Roadmap|Roadmap]]
