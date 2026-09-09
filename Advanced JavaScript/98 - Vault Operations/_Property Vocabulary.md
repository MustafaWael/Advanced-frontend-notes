---
tags: [vault-ops]
module: "98 - Vault Operations"
priority: important
status: learning
---

# Property Vocabulary

The allowed values for this vault's frontmatter properties, and the reason this note carries `status: learning`.

## Why this note exists

Obsidian's Properties panel has no fixed option list for a text property. Its autocomplete dropdown is built from **values already used somewhere in the vault** — so a value that no note uses is a value you cannot pick, only type by hand.

Until this note existed, zero notes used `status: learning`, so it never appeared in the dropdown. This note carries it deliberately, as the seed value.

It is safe here: every `Base.base` view filters out `98 - Vault Operations`, the Status-Driven Quiz Queue ignores it, and `Scripts/status-audit.py` excludes the folder too. It is a dictionary entry, not a study note.

> [!warning] Do not "fix" this note's status to `not-started`. Doing so removes `learning` from the vault and the autocomplete option disappears again — along with the Quiz Pool and Study Queue views, which filter on exactly that value.

## `status`

| Value         | Meaning                                                                                       |
| ------------- | --------------------------------------------------------------------------------------------- |
| `not-started` | Written but never studied. Default for every new note.                                        |
| `learning`    | Actively being studied or drilled. **This is the value every status-driven view filters on.** |
| `solid`       | Two clean quiz passes in separate sessions. Spot-check only.                                  |

Transitions — see [[18 - Revision Plans/07 - Status-Driven Quiz Queue|Status-Driven Quiz Queue]]:

- Open a note to study it → `learning`
- Two clean passes, separate sessions → `solid`
- Miss the mechanism on a `solid` spot-check → back to `learning`, same day

## `priority`

| Value | Meaning |
| --- | --- |
| `must-know` | Interview surface. Drill first. |
| `important` | Expected of a strong candidate; second pass. |
| `deep-dive` | Depth for its own sake. Never blocks a plan. |

There is no `optional`.

## Other properties

- `module` — quoted, exactly matching the folder name: `"09 - Event Loop Advanced"`.
- `aliases` — alternate names for link resolution.
- `verified_on` / `version_scope` — version-sensitive notes only (React, Next.js, TypeScript, test tooling). Flagged by the status audit once older than 90 days.

## Related Notes

- [[18 - Revision Plans/07 - Status-Driven Quiz Queue|Status-Driven Quiz Queue]]
- [[98 - Vault Operations/Templates/Concept Note Template|Concept Note Template]]
