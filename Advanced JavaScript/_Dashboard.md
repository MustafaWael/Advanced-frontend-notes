---
tags: [javascript, dashboard]
module: "Vault Root"
priority: must-know
status: not-started
---

# Dashboard

Your study control center. Update the `status` field in each note's frontmatter as you learn: `not-started` → `learning` → `solid`.

> [!tip] No plugins needed: use the Base
> **[[Base.base|Base]]** (Obsidian's built-in Bases feature) is the primary control center — open it for the **Study Queue**, **Must Know**, **Learning**, **Solid**, **Not Started**, **Deep Dive Queue**, and **Version-Sensitive (re-verify)** views. The "Version-Sensitive" view lists notes with a `verified_on` date (React/Next/tooling facts that age) — oldest first, so you know what to re-check against official docs.

> [!tip] Optional community plugins (everything below this callout requires **Dataview**)
> - **Dataview** — powers the live tables below; skip them if you prefer the Base.
> - **Spaced Repetition** — turn the practice Q&As into scheduled flashcards.
> - **Canvas** (core plugin) — consider rebuilding the dependency map in [[01 - Roadmap|Roadmap]] as a visual canvas.

## Progress by Status (Dataview)

```dataview
TABLE WITHOUT ID file.link AS Note, module AS Module, priority AS Priority
FROM ""
WHERE status = "learning"
SORT module ASC
```

```dataview
TABLE WITHOUT ID length(rows) AS Count, status AS Status
FROM ""
WHERE status
GROUP BY status
```

## Must-Know Notes Not Yet Solid

```dataview
TABLE WITHOUT ID file.link AS Note, module AS Module, status AS Status
FROM ""
WHERE priority = "must-know" AND status != "solid" AND !contains(file.name, "MOC") AND !contains(file.name, "Checklist")
SORT module ASC
LIMIT 40
```

## Notes by Module

```dataview
TABLE WITHOUT ID length(rows) AS Notes, module AS Module
FROM ""
WHERE module
GROUP BY module
SORT module ASC
```

## Deep-Dive Queue (senior signal)

```dataview
LIST
FROM ""
WHERE priority = "deep-dive" AND status = "not-started"
SORT file.folder ASC
```

## Fallback Navigation (no plugins needed)

- [[00 - Start Here|Start Here]] — how to study this vault
- [[01 - Roadmap|Roadmap]] — full dependency-ordered path
- Module MOCs: each numbered folder has a `00 - … MOC` note with reading order
- [[90 - Labs/00 - Labs MOC|Labs]] — build briefs that turn notes into muscle memory
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Checklist]] — the full readiness audit
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]] · [[18 - Revision Plans/03 - 14 Day Deep Study Plan|14 Day Deep Study Plan]]
- [[99 - Glossary|Glossary]] — precise terms
- [[98 - Vault Operations/00 - Vault Operations|Vault Operations]] — templates and vault conventions

## Weekly Ritual

1. Open the Base's **Must Know** view (or the Dataview table above) and pick 3 notes.
2. For each: study loop from [[00 - Start Here|Start Here]], then promote its `status`.
3. Solve 5 questions from [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]].
4. Demote any note back to `learning` if you failed its practice questions.
5. Log it with the [[98 - Vault Operations/Templates/Weekly Review Template|Weekly Review Template]].
