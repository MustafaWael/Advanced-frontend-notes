# GreatFrontEnd: Front End System Design Playbook

> Source: https://www.greatfrontend.com/front-end-system-design-playbook
> Last studied: 2026-07-17

The Front End System Design Playbook by GreatFrontEnd (Yangshun Tay, ex-Meta Staff Engineer) is the most comprehensive front-end-specific system design resource. System design rounds heavily influence hire decision AND leveling — for senior+ a weak round almost always means rejection.

## Structure of the source

1. **Techniques and guides** — 6 articles (~51 min total): Introduction, Types of questions, RADIO framework, Evaluation axes, Common mistakes, Cheatsheet. All free.
2. **Practice questions** — 20 solved system design questions (~12h total). Free: News Feed, Autocomplete. Premium: the other 18.

## This folder

- `knowledge_base/01_introduction.md` — FE vs BE system design, why generic resources mislead
- `knowledge_base/02_types_of_questions.md` — Applications vs UI components, full topic-per-app table
- `knowledge_base/03_radio_framework.md` — the core framework, in depth with examples
- `knowledge_base/04_evaluation_criteria.md` — the 6 evaluation axes and RADIO mapping
- `knowledge_base/05_common_mistakes.md` — 6 common pitfalls and fixes
- `knowledge_base/06_cheatsheet.md` — one-page recap
- `questions/01 - News Feed (Facebook).md` — full solved case study (application type)
- `questions/02 - Autocomplete.md` — full solved case study (UI component type)
- `01_guides.md` / `02_practice_questions.md` — indexes with links

## Key takeaways

- Front end system design = client architecture + client-server API boundary. Treat the server as a black box. No capacity estimation. Focus areas: performance, UX, accessibility, i18n — not scalability/consistency/availability.
- Use **RADIO**: Requirements (~10%), Architecture (~20%), Data model (~10%), Interface (~20%), Optimizations/deep dive (~40%).
- Interviewers score *observed* signals — verbalize every tradeoff and decision.
- Let the product category pick the deep-dive topics (SEO for commerce, real-time protocols for chat, streaming for video, conflict resolution for collaboration).
