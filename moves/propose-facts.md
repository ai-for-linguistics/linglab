---
name: linglab-propose-facts
description: "Propose candidate facts (minimal pairs, elicitation lists) that separate tied theories in a linglab project, marked as low-confidence proposals, never as data. Use when several theories tie and new data is needed to tell them apart."
---

# propose-facts

**Use when** several theories tie, and you need data that tells them apart.

**Read** the matrix; the theories' differing principles; their predictions (which theories pass or fail a candidate).

**Produce** candidate facts in `data/statements.json` with `origins` source `user` or yours, low `confidence` until a native speaker or a paper confirms, and a note of which theories it separates. Offer an elicitation list (sentences to ask informants) in chat or as a view; do not invent judgments and present them as data. Run the candidates to show which theories each separates.

**Pitfalls**
- A proposed fact is not data until someone judges it. Mark the source honestly.
- Prefer minimal pairs that differ in one principle's prediction.
- Check the candidate in Raw Facts for consistency with existing facts (`listing`).
- Do not add many facts at once; the page gets noisy and review gets skipped.

**Prompt**
> Which of the top theories on the page are hardest to tell apart? Propose up to five new facts that separate them, each with the sentences, the expected judgment per theory, and what to ask a speaker. Add them as low-confidence facts from "proposal", not as data.
