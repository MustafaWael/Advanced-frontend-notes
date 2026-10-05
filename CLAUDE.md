# CLAUDE.md — Mid-Level Frontend Interview Coach

The working rules for this vault live in `AGENTS.md`: who the learner is, how deep to go per module, the accuracy contract, and the other vault skills. Read them before any vault work:

@AGENTS.md

## Writing and upgrading notes: use `human-first-guides`

Every note in this vault should be followable by a smart reader who is new to the topic, reading top to bottom, without opening another tab. The `human-first-guides` skill holds that standard:

- every term is explained before it's used;
- smaller concepts get short primers;
- the plain idea comes before the official name;
- the guide follows one spine;
- "because" lines replace topic lists;
- confusing pairs are named;
- notes link to each other;
- AI tells are cut;
- examples and use cases are the frame of the guide.

Use it together with the vault's other note skills:

- `vault-note-authoring` owns the file: template, frontmatter and placement.
- `add-use-cases` owns the Real-World Use Cases section.
- `human-first-guides` owns how the note teaches.

### When to invoke it

Invoke `human-first-guides` whenever a request is about how a note teaches, even if the skill isn't named:

- **Writing a new note or guide.** For example, "write a note on structured clone" or "draft the closures note". Use it with `vault-note-authoring`.
- **A note that's hard to follow.** For example, "I don't get this paragraph", "this note has gaps", "you didn't explain X" or "too much jargon".
- **Upgrading or reviewing a note.** For example, "upgrade note 03", "review this note", "apply the skill to X" or "make this human-friendly". An upgrade starts with a diagnosis and a plan in tiers, and nothing changes until the plan is approved.
- **Smaller concepts used without explanation.** For example, "give me a short summary of these sub-concepts" or "what does each of these terms mean here?"
- **Concepts that feel disconnected.** For example, "how does X connect to Y?", "this reads like separate boxes" or "link this note to the rest of the module".
- **Missing examples and use cases.** For example, "add examples", "I need use cases to connect this" or "where does this show up in real code?". Pair it with `add-use-cases` for the Real-World Use Cases section.
- **A "Why It Matters" list.** Turn it into because-lines.
- **Wording that reads as AI-written.** Remove the AI tells.
- **Text brought in from a chat or another AI.** Before it goes into a note, run the skill's accuracy pass and term ledger on it.

Don't use it for quizzing (`frontend-interview-griller`), running labs (`lab-runner`) or study planning (`spaced-review-scheduler`).

### Where the skill lives

- It is saved as an account skill.
- A copy is in `.agents/skills/human-first-guides/SKILL.md`.
- Another copy belongs in `.claude/skills/human-first-guides/SKILL.md`, next to the other vault skills.

All three copies must stay identical, so when the skill changes, update all three together.
