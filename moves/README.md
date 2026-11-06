# moves: short playbooks

Tips, not procedures. Open one when its situation comes up. Each has: when to use it, what to read, what to produce, pitfalls, a prompt the user can paste.

A playbook that starts with skill frontmatter (`name: linglab-<file name>`, and a `description` saying what it does and when to use it) can be installed with `linglab init --claude-skills` or `linglab skills` as a Claude Code skill (`.claude/skills/<name>/SKILL.md` in the project); `linglab skills` refreshes the installed copies after the toolkit is replaced. Give a new playbook frontmatter unless it is not a situation-triggered procedure (like this index and `possibilities.md`). Inside a playbook, refer to another one by its path from the project root (`utils/moves/prove.md`): the installed copies live elsewhere.

- `extract-facts.md`: data from a paper into facts.
- `extract-principles-and-theories.md`: a paper's assumptions into principles and theories.
- `propose-principles.md`: new or repaired principles, compression.
- `propose-facts.md`: facts that separate the top theories.
- `new-fragment.md`: building a new fragment: models, values, principles, operators over other worlds.
- `prove.md`: getting a claim to a verifier: statement first, countermodel first, parallel tracks, lemma kits, traps.
- `check.md`: informal, Python, Lean; the `linglab` commands.
- `review-a-paper.md`: the seven checks.
- `read-and-plan.md`: answering from the data, what to gather next.
- `make-a-view.md`: custom views and other formats.
- `possibilities.md`: ideas to keep in mind and to propose when the time comes (not features to build now).

Always: honest status labels, small steps, rebuild the page and say where to look (`python3 utils/bin/linglab.py report`).
