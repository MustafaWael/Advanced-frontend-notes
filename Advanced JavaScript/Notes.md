
##SSR Hooks
Core Technical Rules for SSR Hooks

- **Avoid Top-Level Browser APIs**: Do not reference global objects like `window`, `document`, `navigator`, or `localStorage` directly in the main body of your hook. Node.js environments do not have these APIs, causing the server to throw an error like `window is not defined`. [[1](https://stackoverflow.com/questions/67293649/how-to-use-hook-in-server-side-render-on-next-js), [2](https://ahooks.js.org/guide/blog/ssr/)]

- **Isolate Side Effects**: Wrap all browser-specific operations inside a `useEffect` hook. React entirely skips `useEffect` execution on the server side. [[1](https://www.youtube.com/watch?v=BMHmyP3-rAk&t=86), [2](https://www.youtube.com/watch?v=om3Z-CbtR3Q&t=23), [3](https://rangle.io/blog/building-react-components-with-server-side-rendering-in-mind), [4](https://stackoverflow.com/questions/59187066/how-to-perform-a-server-side-data-fetching-with-react-hooks)]

- **Provide Fallback States**: Initialize state variables with safe default values (like `null`, `false`, or an empty string) that make sense on the server. [[1](https://reactuse.com/blog/react-browser-api-hooks/), [2](https://sap.github.io/spartacus-docs/server-side-rendering-optimization/), [3](https://dev.to/hiteshchawla/using-custom-react-hooks-in-nextjs-3gjo)]

- **Avoid useLayoutEffect**: Do not use `useLayoutEffect` inside hooks meant for SSR. It runs synchronously after DOM mutations, causing explicit console warnings on the server. Use `useEffect` instead. [[1](https://www.geeksforgeeks.org/reactjs/server-side-rendering-ssr-with-react-hooks/), [2](https://gist.github.com/gaearon/e7d97cdf38a2907924ea12e4ebdf3c85)]

❌ Breaking SSR (Bad Pattern)

This custom hook will crash your application on the server because `window` is called directly during the initial execution phase. [[1](https://ahooks.js.org/guide/blog/ssr/), [2](https://dev.to/hiteshchawla/using-custom-react-hooks-in-nextjs-3gjo)]

“If you use these properties directly, you will get errors like window is not defined, document is not defined, navigator is not defined , etc. A common misuse is that global properties, such as document, are used directly during the execution of Hooks.”, as noted by [ahooks](https://ahooks.js.org/guide/blog/ssr/).

javascript

```
import { useState } from 'react';

// 🔴 CRASHES ON SERVER
export function useWindowWidth() {
  const [width, setWidth] = useState(window.innerWidth); 
  return width;
}
```

Use code with caution.

Fixing it for SSR (Good Pattern)

By using `useEffect` and an architectural guard clause, the server securely bypasses the window calculation. [[1](https://dev.to/neetigyachahar/server-side-rendering-ssr-vs-react-server-components-rsc-in-nextjs-the-use-client-directive-4kd6), [2](https://reactuse.com/blog/react-browser-api-hooks/)]

javascript

```
import { useState, useEffect } from 'react';

//  SSR SAFE
export function useWindowWidth() {
  const [width, setWidth] = useState(null); // Safe server default

  useEffect(() => {
    // Only runs on the client browser
    setWidth(window.innerWidth);
    
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return width;
}
```

Use code with caution.

Summary of Hook Behavior in SSR

|React Hook|Runs on Server?|Safe to Use?|
|---|---|---|
|`useState`|Yes (for initial value)|Yes|
|`useMemo` / `useCallback`|Yes|Yes|
|`useEffect`|**No**|Yes (safest place for browser-only code)|
|`useLayoutEffect`|**No**|No (triggers server warnings)|
|`useSyncExternalStore`|Yes|Yes (excellent for matching client/server state)|

If you are using modern framework variants like Next.js **App Router**, ensure any files containing client-side state hooks contain the `"use client"` directive at the very top. This tells the compiler to treat the file as a client boundary, though it still undergoes initial server pre-rendering. [[1](https://www.reddit.com/r/nextjs/comments/1ezamqy/using_react_hooks_with_nextjs_is_really_confusing/), [2](https://github.com/vercel/next.js/issues/52566), [3](https://www.reddit.com/r/reactjs/comments/13w00an/usehooks_a_collection_of_server_component_safe/)]

If you are struggling with a specific code snippet, share your **custom hook logic** or the exact **error message** you are seeing, and I can refactor it to be fully **SSR-compatible** for you. [[1](https://www.dhiwise.com/post/how-to-fix-useeffect-not-triggering-in-your-react-project), [2](https://dev.to/hiteshchawla/using-custom-react-hooks-in-nextjs-3gjo)]