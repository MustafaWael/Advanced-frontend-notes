---
tags: [networking, dns, infrastructure]
module: "26 - How the Web Works"
priority: important
status: not-started
aliases: [Domain Name System, How domains work]
---

# DNS and Domains

## Maturity Target

- Priority: #important
- Study time: 35 minutes
- Interview signal: Trace a DNS lookup through its full cache chain and explain records (A, AAAA, CNAME) and TTL tradeoffs without notes.
- Production signal: You can debug "site works on my machine, down for users in region X", reason about DNS in deploy/rollback plans, and know why `dns-prefetch` exists.
- Dependencies: [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]

## Source Anchors

- [MDN - What is a domain name?](https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Web_mechanics/What_is_a_domain_name)
- [Cloudflare - What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/)
- [RFC 1034 - Domain Names: Concepts and Facilities](https://datatracker.ietf.org/doc/html/rfc1034)

## 1. Concept

Simple version: DNS is the internet's phone book — it translates a human-readable name (`app.example.com`) into an IP address machines can route to. It's a distributed, hierarchical database with aggressive caching at every layer.

The accurate mechanism. A domain reads right-to-left as a hierarchy: `.` (root) → `com` (TLD) → `example` (the registered/apex domain) → `app` (subdomain). Resolution walks that hierarchy, but only after exhausting caches:

1. **Browser DNS cache** — per-browser, short-lived.
2. **OS cache** (+ `hosts` file) — the stub resolver.
3. **Recursive resolver** — usually your ISP's or a public one (1.1.1.1, 8.8.8.8). This is where most cache hits happen.
4. **Full recursion** on a miss: root server → `.com` TLD server → `example.com`'s **authoritative nameserver**, which holds the actual records.

Every record carries a **TTL** (seconds) that says how long caches may keep it. That single number is the tradeoff dial: long TTL = fewer lookups, faster; short TTL = faster failover/migration, more lookups.

Records frontend devs actually meet:

```text
A       example.com      → 93.184.216.34        (name → IPv4)
AAAA    example.com      → 2606:2800:220:1::34  (name → IPv6)
CNAME   www.example.com  → example.com           (alias → another name)
CNAME   app.example.com  → cname.vercel-dns.com  (how you point at Vercel/Netlify)
TXT     example.com      → "v=spf1 ..."          (domain verification, email auth)
NS      example.com      → ns1.registrar.com     (who is authoritative)
```

A CNAME means "ask again with this other name" — it adds a lookup but lets a platform (CDN, host) change its IPs without you touching your DNS. That's why hosting providers hand you a CNAME target, and why the apex domain (which historically can't be a CNAME) needs `ALIAS`/`ANAME`/flattening workarounds.

## 2. Why It Matters

- "How do domains work?" is a foundations question that separates devs who deploy from devs who only code.
- DNS is stage one of every uncached page load — a slow resolver adds latency *before* your performance budget even starts.
- Deploys and incidents: DNS-based failover is only as fast as your TTL. Migrations get planned around "lower TTL a day before, switch, raise it back."
- Same-origin policy is defined on scheme+host+port — meaning `app.example.com` and `api.example.com` are different origins, which is a DNS-naming decision with CORS and cookie consequences ([[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: you migrate the API from one provider to another. You update the `api.example.com` A record at 10:00. By 10:05 your own testing works. Support tickets keep arriving until the next afternoon: some users still hit the old, now-dead IP.

Trace: the old record had `TTL 86400` (24h). Every recursive resolver that cached it before 10:00 keeps answering with the stale IP until its copy expires. Nothing you do server-side can flush other people's resolvers.

```text
# Fix: plan TTLs around the migration
# T-48h:  api.example.com  A  <old-ip>  TTL 300     ← lower TTL, let 24h caches drain
# T-0:    api.example.com  A  <new-ip>  TTL 300     ← switch; worst-case staleness now 5min
# T+24h:  api.example.com  A  <new-ip>  TTL 3600    ← raise once stable
# Keep the old backend serving (or redirecting) during the overlap window.
```

Tradeoffs: low TTLs increase lookup traffic and make you more dependent on resolver availability; keeping the old backend alive during overlap costs money. The general lesson: DNS changes are *eventually consistent* — design cutovers with overlap, never a hard switch.

> [!tip] Frontend-visible lever: `<link rel="dns-prefetch" href="https://api.example.com">` (or the stronger `preconnect`) resolves third-party domains during idle time, shaving the DNS+connection cost off the first real request.

## 4. Interview Answer

Short answer:

> DNS maps names to IPs through a hierarchy — root, TLD, authoritative nameservers — but in practice most lookups are served from caches: browser, OS, then a recursive resolver. Records like A/AAAA map names to IPs, CNAME aliases one name to another, and every record has a TTL controlling how long caches keep it. That TTL is the core tradeoff: long means fast and stable, short means you can fail over or migrate quickly.

Deeper answer:

> Deeper: resolution is recursive from the client's view but iterative at the resolver — it queries root, TLD, and authoritative servers step by step and caches each answer. CNAMEs are how CDNs and hosts stay re-pointable; apex domains need ALIAS/flattening because a CNAME can't coexist with other record types at the apex. Operationally, DNS is eventually consistent, so migrations are planned as TTL-lowering, overlap, then switch. For frontend perf, DNS is part of the pre-TTFB waterfall — `dns-prefetch`/`preconnect` hide it, and DoH/DoT change privacy but not the mechanics.

## 5. Practice

1. <details><summary>Walk the full resolution path for a cold lookup of app.example.com.</summary>Browser cache miss → OS stub resolver miss → recursive resolver miss → resolver asks root ("who handles .com?") → TLD server ("who is authoritative for example.com?") → authoritative nameserver returns the A/AAAA (or CNAME) record → each layer caches it for TTL seconds.</details>
2. <details><summary>Why did users still hit the old server a day after you changed the record?</summary>The old record's 24h TTL was cached by recursive resolvers worldwide. Caches expire on their own schedule; you can't invalidate them remotely. Prevention: lower TTL before the change and keep the old target serving during the overlap.</details>
3. <details><summary>Your app calls three third-party origins (fonts, analytics, API). What DNS-related optimization applies and what does it cost?</summary>`preconnect` (DNS + TCP + TLS) for the critical one(s), `dns-prefetch` for the rest. Cost: preconnect holds a socket open speculatively — wasted work if the origin is never used, so reserve it for origins you will certainly hit early.</details>

## Related Notes

- [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]
- [[26 - How the Web Works/03 - Connection Layer|Connection Layer]]
- [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
