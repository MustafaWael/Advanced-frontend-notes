---
tags: [interview, communication, behavioral, tradeoffs]
module: "15 - Interview Preparation"
priority: important
status: not-started
---

# Explaining Tradeoffs to Non-Engineers

## Maturity Target

- Priority: #important
- Study time: 45 minutes + one rehearsal per scenario
- Interview signal: when asked "how would you explain this to a PM?", you translate to outcomes and risk without becoming vague or condescending.
- Production signal: your estimates and pushbacks get accepted because they're framed in the listener's currency.
- Fast track: rehearse the three scenarios below out loud, one minute each.

## The Mechanism

Translating for non-engineers is not simplifying — it's **changing the unit of account**. Engineers argue in mechanisms (bundle size, race conditions, cache invalidation); product people decide in outcomes (user impact, risk, time, optionality). A tradeoff explanation lands when every technical cost is converted:

| Engineer's currency | Translated currency |
| --- | --- |
| "This adds tech debt" | "Shipping this way is faster now, but the next three features in this area get ~30% slower" |
| "The bundle gets big" | "Slower first load, mostly for mobile users — which is most of our signup traffic" |
| "There's a race condition" | "Occasionally a user will see yesterday's price and we'll honor a wrong number" |
| "We should refactor first" | "One week now buys us shipping the next two requests in days instead of weeks" |

Three rules that carry the conversation:

1. **Lead with the recommendation, not the analysis.** "I recommend B. Here's the cost of each option" beats a guided tour of your reasoning. Decision-makers ask for the reasoning they need.
2. **Give real options, priced.** "Option A: 2 days, works until ~10k items. Option B: 2 weeks, scales past that. Given the roadmap, A — we revisit when the catalog grows." One option is a lecture; unpriced options are a quiz.
3. **Name the reversibility.** "This is easy to change later" vs "this locks us in" is often the only technical property a PM *needs*. Reversible → decide fast, ship. Irreversible → slow down, escalate.

> [!warning] The failure modes are symmetric: jargon ("hydration mismatch causes CLS") loses them; over-simplifying ("it'll just be slow") loses their *trust*, because it's unfalsifiable. The fix for both is the same — concrete user-visible consequence plus a number, even a rough one.

## Rehearsal Scenarios

Answer each out loud, ~60 seconds, before opening the hint.

1. <details><summary>PM: "Can we skip the loading-state work and ship Friday?"</summary>Structure: recommendation → priced consequence → smaller alternative. "We can, and here's what users experience: on slow connections the page looks frozen for 2-4 seconds and some will double-submit orders — that's a support-ticket generator, not just polish. Middle option: I ship the two states on the checkout path Friday and defer the rest — that's the 20% covering the risky flows."</details>
2. <details><summary>PM: "Why does 'just add a filter dropdown' take a week?"</summary>The honest breakdown, in outcome terms — never "it's complicated." "The dropdown is a day. The week is: filters have to survive page reload and be shareable as links (that's URL state), combine with the existing sort without showing stale results (that's the request layer), and work for keyboard users (that's compliance risk if skipped). I can cut scope: no shareable URLs saves two days — do we need them?" Making the invisible work visible *as features they chose* turns an estimate fight into a scope decision.</details>
3. <details><summary>Stakeholder: "Competitor X shipped this in a weekend."</summary>Don't defend; reprice. "Maybe — a demo of this is a weekend for us too. The gap is the failure modes: what happens on flaky networks, on a 3-year-old phone, for the 8% on screen readers. We could ship the weekend version behind a flag to 5% and measure — I'm fine with that if we agree what error rate makes us pull it." Converting the challenge into an experiment with an agreed kill-switch turns a status fight into a shared decision.</details>

## Related Notes

- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
- [[15 - Interview Preparation/09 - Architecture Disagreements and Ownership Stories|Architecture Disagreements and Ownership Stories]]
- [[29 - Frontend System Design/01 - The Frontend System Design Framework|The Frontend System Design Framework]]
