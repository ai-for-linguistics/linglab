---
name: linglab-propose-principles
description: "Propose fixes, variants or compressions of theories in a linglab project (new principles, smaller theories with the same coverage) and state what each gains and loses in facts. Use when a theory fails facts the user cares about, or to look for a smaller theory with the same coverage."
---

# propose-principles

**Use when** a theory fails facts you care about, or you want a smaller theory with the same coverage.

**Read** the matrix (`data/results.json`), failed facts and their `reasons` (countermodels), the principles and `relations`, `data/metrics.json`.

**Produce** new principles and theories: `kind: fix` (parent set; smallest change), `creative`, or compressions (fewer principles, same facts). Record each with its fix reason in `notes`. Run `run`, `metrics`, `report`; state the gain and the loss in facts.

**Pitfalls**
- Always give the cost of a fix: which other facts it loses. Re-run the whole table.
- Look for the non-collapse partner of a positive fact (must stay consistent, must not entail everything). Collapsing theories win on raw coverage.
- Borrow a principle from another paper if it is the cheapest repair.
- Sweeps over principle sets are costly: state the number of candidates and the estimated cost first. Cheap reasoning before search.
- Say what space an exhaustive claim covers ("no set in these 22 principles"), not more.
- Creative proposals are labelled as ours, and unverified until run.

**Prompt**
> Theory `<T-..>` fails `<facts>`. Propose the smallest fix as a new theory with parent `<T-..>`. Run it on all facts and tell me what it gains and what it loses. If you want to search many combinations, tell me the number and the cost first.
