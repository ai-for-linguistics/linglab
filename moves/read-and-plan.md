---
name: linglab-read-and-plan
description: "Answer questions about the state of a linglab project from its data files, with honest labels (kind of evidence, bound, confidence), and plan what to gather next with its cost. Use when the user asks where things stand, wants a summary, or asks what to do next."
---

# read-and-plan

**Use when** the user asks a question about the state of the project, or wants a summary or a plan.

**Read** the data files, not memory: `data/results.json` (pooled by the ladder), `findings.json`, `metrics.json`, `meta.json`. Run `check` and `report` first if data changed.

**Produce** an answer in chat with each claim labelled: kind (lean, python, human, paper-claim, ...), bound, confidence, contested, conflicts and warnings. For a summary: the top theories by the metric the user prefers, what they fail, what is out of scope, what is pending. For a plan: what data to gather next (facts that separate the top theories, papers not yet read, cells pending), the cost of each in compute and tokens, one suggested next step. Store durable conclusions in `data/findings.json` with a status.

**Pitfalls**
- Do not claim more than the status supports. Say "in this fragment" and name the bound.
- State which switches (llm-judged, system facts, contested) the numbers use.
- Do not rank arbitrary choices; show the frontier and let the user pick the metric.
- Check before answering: re-read the cell, not your last summary.
- Distinguish pending, failed, out of scope.

**Prompt**
> Where do we stand? Summarize the top theories by coverage and size, what they fail, what is pending or out of scope, with the kind of evidence for each. Then tell me what data to gather next and what it would cost.
