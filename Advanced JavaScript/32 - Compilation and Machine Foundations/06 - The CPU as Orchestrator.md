---
tags: [machine-model, hardware, performance]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [MMIO, DMA, Interrupts, How the CPU Talks to Devices, GPU vs CPU]
---

# The CPU as Orchestrator

## Maturity Target

- Priority: #deep-dive
- Study time: 20-30 minutes
- Interview signal: you can explain how a CPU reaches RAM, a GPU and a network card, and why DMA and interrupts exist — then connect it to transferable buffers and compositor-only animations.
- Production signal: you understand why `transform`/`opacity` animations are cheap, why `getImageData` stalls, and why transferring an `ArrayBuffer` to a worker beats copying it.
- Dependencies: [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]]

## Source Anchors

- [Chrome - RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)
- [MDN - Transferable objects](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Transferable_objects)
- [MDN - WebGPU API](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API)
- [web.dev - Animations and performance](https://web.dev/articles/animations-guide)

## 1. Concept

**Simple explanation.** The CPU does not contain the rest of the computer; it talks to it. RAM, GPU, disk and network card are separate chips, and the CPU reaches them by writing to addresses. For anything large it delegates the copying, and it finds out when work finished by being interrupted.

**Accurate mechanism.** Four mechanisms, in increasing order of indirection.

**1. RAM — direct, address-based.** The memory bus is wired to the CPU, and the instruction set has dedicated load/store instructions. The CPU asserts an address; RAM responds. No software in between.

```asm
mov eax, [0x1000]   ; CPU puts 0x1000 on the bus; RAM returns those bits
mov [0x1000], eax   ; CPU puts address + data; RAM stores it
```

**2. Devices — memory-mapped I/O.** Certain address ranges are not wired to RAM chips at all; the chipset routes them to a device's control registers. So the CPU still executes an ordinary store — it has no concept of "network card":

```asm
mov [0xFED00000], eax   ; looks like a memory write; the motherboard routes
                         ; this range to a device's registers, not to RAM
```

**3. Drivers — the protocol, in software.** Knowing *which* magic addresses a specific chip expects, in what order, is what a device driver is: ordinary compiled code running on the CPU, translating "send this packet" into the exact sequence of register writes that chip requires. Your application calls an OS API; the driver does the register choreography.

**4. DMA — delegate the bulk copy.** Having the CPU copy a 40 MB texture byte by byte would waste it. Instead the CPU tells the device, via MMIO, "here is an address and a length — fetch it yourself." The device's own controller reads and writes RAM directly, without the CPU in the loop, and signals when done. **The CPU orchestrates; it does not personally move every byte.** That sentence is the whole note.

**5. Interrupts — being told, not asking.** A device cannot call a function on another chip. When a packet arrives or a disk read completes, it raises an electrical interrupt line. The CPU suspends the current instruction stream, jumps to a handler installed by the OS, deals with it, and resumes. The alternative — polling — burns cycles asking "are you done yet?"

### The GPU is not a device; it is a second computer

Worth separating, because it changes how you reason about frontend performance:

```txt
your shader / WGSL / GLSL source
   ↓ compiled by a GPU compiler shipped in the driver
GPU machine code — a completely different ISA, massively parallel
   ↓ CPU copies code + data into GPU memory (MMIO for commands, DMA for bulk)
   ↓ CPU writes a control register: "execute"
GPU's own execution units run it, in parallel, while the CPU does other work
   ↓ GPU raises an interrupt when finished
CPU reads results back
```

The GPU has its own version of everything in this module — its own compiler pipeline, its own instruction set, its own memory. The CPU's role really is orchestration: upload, launch, be notified, read back.

### The frontend echoes of each mechanism

This is not a metaphor; these APIs exist because of the hardware facts above.

| Hardware fact | What you see in the browser |
| --- | --- |
| Bulk copies are delegated, not performed | `postMessage(buf, [buf])` **transfers** ownership of an `ArrayBuffer` with no copy; the sender's view is detached |
| The GPU runs independently, in parallel | `transform` and `opacity` animations run on the compositor and keep moving even while the main thread is busy |
| Reading back from the GPU requires a round trip | `canvas.getImageData()` and `gl.readPixels()` stall, because the CPU must wait for the GPU |
| Devices are asynchronous and interrupt you | Every I/O callback in the event loop — the host is notified, then enqueues a task |
| The GPU has its own compiler | Shader compilation is a real, measurable cost; WebGPU exposes explicit pipeline creation so you can pay it up front |

> [!warning] "It's on the GPU so it's free" is where jank comes from
> A property that only affects compositing (`transform`, `opacity`) can be handled by the compositor without the main thread. A property that changes geometry (`width`, `top`, `margin`) forces layout and paint on the main thread first, no matter how it is animated. Animating `left` instead of `transform` is not a style preference; it moves the work to a different processor.

## 2. Why It Matters

- It turns three separate performance rules — transfer instead of copy, animate compositor properties, avoid canvas readback — into one mechanism you can derive rather than memorize.
- It explains why offloading is asynchronous everywhere: separate processors are notified, never called.
- It grounds the event loop's I/O side in something physical: interrupts are why a task queue exists at all.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A photo editor sends a full-resolution bitmap to a worker for filtering. The UI freezes for ~180 ms per filter change, and the worker was supposed to prevent exactly that.

```ts
// ❌ postMessage without a transfer list: structured clone copies the buffer
const pixels = ctx.getImageData(0, 0, 6000, 4000); // ~96 MB, and a GPU→CPU readback
worker.postMessage({ pixels });                     // the whole thing is *copied*
```

Trace, in two parts. First, `getImageData` forces a readback from the GPU-backed canvas surface into CPU-visible memory — the main thread waits on another processor. Second, `postMessage` with no transfer list structured-clones the payload: the 96 MB buffer is duplicated, on the main thread, synchronously enough to blow the frame budget. The worker never got a chance to help.

```ts
// ✅ Transfer ownership instead of copying, and keep pixels off the main thread
const bitmap = canvas.transferControlToOffscreen();   // hand the surface to the worker
worker.postMessage({ bitmap }, [bitmap]);             // transfer, not copy

// and for raw buffers you do need to move:
const buf = new Uint8ClampedArray(byteLength).buffer;
worker.postMessage({ buf }, [buf]);                   // zero-copy; buf is now detached here
```

`OffscreenCanvas` lets the worker own the drawing surface, so the readback and the filtering both happen off the main thread; a transfer list moves buffer ownership rather than duplicating bytes — the software-level version of handing a device an address instead of copying through the CPU.

Tradeoffs: after a transfer the sender's view is **detached** and any further access throws, so ownership has to be tracked deliberately; `OffscreenCanvas` splits your rendering code across two files and two debuggers; and returning results still costs a transfer, so an interaction that needs pixels back on the main thread every frame may not win at all.

> [!tip] Copy, transfer, or share
> Three distinct choices with three cost profiles: structured clone (copy — simple, O(bytes), main-thread cost), transfer (move — zero-copy, sender loses access), `SharedArrayBuffer` (share — no copy either way, but requires COOP/COEP and real synchronization discipline; see [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm, Agent and Job Queue]]).

## 4. Interview Answer

Short answer:

> The CPU is the orchestrator, not the container. It reaches RAM directly over the memory bus with load/store instructions, and reaches devices the same way — except those addresses are routed to device control registers instead of RAM, which is memory-mapped I/O. Drivers are the software that knows each chip's register protocol. For bulk data the CPU hands the device an address and a length and lets it copy itself, which is DMA, and devices signal completion by raising an interrupt rather than being polled.

Deeper answer:

> The GPU is the case worth separating: it is not a device the CPU pokes but a second processor with its own instruction set, its own compiler shipped in the driver, and its own memory, running in parallel once launched. The CPU uploads code and data, writes a control register to start it, and gets an interrupt when it finishes. That is why compositor-only properties like `transform` and `opacity` keep animating while the main thread is blocked, and why `getImageData` or `readPixels` stalls — you are forcing a synchronous round trip to another processor. The same shape shows up in the messaging APIs: structured clone is the CPU copying every byte, a transfer list is handing over an address, and `SharedArrayBuffer` is two agents mapping the same memory. Interrupts are also why the event loop has an I/O side at all: nothing calls back into your thread, the host is notified and enqueues a task.

## 5. Practice

1. <details><summary>Why does DMA exist, and what does the CPU still do during a DMA transfer?</summary>Because having the CPU copy megabytes byte by byte wastes a processor that could be running your code. The CPU sets it up — writes the source/destination address and length to the device's registers via MMIO — then goes and does something else. The device's own controller performs the transfer and raises an interrupt when finished.</details>
2. <details><summary>Mechanically, why is animating <code>transform</code> cheaper than animating <code>left</code>?</summary><code>transform</code> can be applied by the compositor, which runs on its own thread and hands the transformation to the GPU; no layout or paint is required, so a busy main thread does not stall the animation. <code>left</code> changes geometry, forcing layout and paint on the main thread every frame — a different processor and a contended one.</details>
3. <details><summary>You <code>postMessage</code> a 50 MB <code>ArrayBuffer</code> to a worker and the main thread janks. What happened, and what are your two alternatives?</summary>With no transfer list, structured clone copied all 50 MB on the main thread. Alternatives: pass the buffer in a transfer list for a zero-copy ownership move (the sender's view becomes detached), or use a <code>SharedArrayBuffer</code> so both agents map the same memory — which needs COOP/COEP headers and explicit synchronization.</details>
4. <details><summary>Transfer: which hardware mechanism is the closest analogue of the event loop's task queue, and why?</summary>Interrupts. A device cannot call into the CPU's current instruction stream, so it raises a signal and the OS handler runs. Likewise a completed <code>fetch</code> cannot call your function directly — the host is notified, enqueues a task, and your callback runs when the current one finishes. Both exist because separate, asynchronous producers cannot interrupt a single-threaded consumer mid-work safely.</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]] — the memory side, one level closer in.
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]] — copy vs transfer vs share, in API terms.
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]] — main thread vs compositor, in production terms.
- [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm, Agent and Job Queue]] — agents and `SharedArrayBuffer`.
- [[26 - How the Web Works/04 - Browser Architecture|Browser Architecture]] — the process model above this hardware model.
