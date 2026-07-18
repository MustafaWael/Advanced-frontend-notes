---
tags: [javascript, scenarios, react, cleaning-event-listeners]
module: "17 - Practical Frontend Scenarios"
priority: must-know
status: not-started
---

# Cleaning Event Listeners

## Maturity Target

- Priority: #must-know
- Study time: 50-70 minutes
- Interview signal: can explain listener identity, cleanup timing, and stale closures.
- Production signal: can prevent duplicate handlers, stale shortcuts, and memory leaks.
- Fast track: sections 2, 4, 5, and 8.

## Source Anchors

- [MDN: addEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener)
- [MDN: removeEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/removeEventListener)
- [MDN: AbortSignal](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## 1. Scenario

A modal opens and closes many times. After a while, pressing Escape runs the close logic multiple times. Or a keyboard shortcut keeps submitting an old query.

Event listener bugs usually come from:

- missing cleanup
- removing with a different function reference
- stale closure inside the handler
- listener options not matching
- registering on every render without intent

## 2. Broken Version

```tsx
function EscapeToClose({ onClose }: { onClose: () => void }) {
  React.useEffect(() => {
    window.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        onClose();
      }
    });

    // BUG: no cleanup, and the inline function cannot be removed later.
  }, []);

  return null;
}
```

## 3. Root Cause

The browser stores the listener function reference. To remove it, you need the same function reference and compatible listener options. An inline arrow passed directly to `addEventListener` cannot be referenced by `removeEventListener`.

The handler also closes over values from the render that created it. Empty deps can produce stale behavior if `onClose` changes.

## 4. Fix: Named Handler With Cleanup

```tsx
function EscapeToClose({ onClose }: { onClose: () => void }) {
  React.useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  return null;
}
```

Tradeoff:

- Simple and correct.
- Re-registers if `onClose` identity changes.
- Parent should stabilize `onClose` if that becomes noisy.

## 5. Fix: AbortSignal Cleanup

Modern `addEventListener` supports `{ signal }`.

```tsx
function EscapeToClose({ onClose }: { onClose: () => void }) {
  React.useEffect(() => {
    const controller = new AbortController();

    window.addEventListener(
      'keydown',
      event => {
        if (event.key === 'Escape') {
          onClose();
        }
      },
      { signal: controller.signal }
    );

    return () => {
      // Removes the listener associated with this signal.
      controller.abort();
    };
  }, [onClose]);

  return null;
}
```

This is useful when one effect registers multiple listeners and you want one cleanup call.

## 6. Fix: Stable Listener With Latest Callback

Use this when the listener should register once but call the latest callback.

```tsx
function EscapeToClose({ onClose }: { onClose: () => void }) {
  const latestOnClose = React.useRef(onClose);

  React.useEffect(() => {
    latestOnClose.current = onClose;
  }, [onClose]);

  React.useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        latestOnClose.current();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return null;
}
```

Tradeoff:

- Stable listener identity.
- Latest callback.
- More mutable code, so use only when registration stability matters.

## 7. Common Bug: Options Mismatch

```tsx
window.addEventListener('scroll', onScroll, { capture: true });

// BUG: capture does not match, so removal can fail.
window.removeEventListener('scroll', onScroll);
```

Pass matching options, especially `capture`.

## 8. Production Checklist

- [ ] Is every listener removed on cleanup?
- [ ] Does cleanup use the same handler reference?
- [ ] Do listener options match?
- [ ] Does the handler close over fresh values?
- [ ] Should the listener be stable and read latest values through a ref?
- [ ] Is the listener passive where appropriate, such as scroll/touch performance?
- [ ] Did Strict Mode reveal duplicate registration in development?

## 9. Interview Angle

Strong answer:

"The browser removes listeners by identity. If I add an inline function and later create a different inline function for cleanup, it will not remove the original listener. In React, I also need to think about stale closures. The normal fix is a named handler inside an effect with cleanup and correct dependencies; for stable global listeners, I can use a ref for the latest callback."

## Related Notes

- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
