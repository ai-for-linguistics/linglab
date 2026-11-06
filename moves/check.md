---
name: linglab-check
description: "Validate a linglab project's data and compute verdicts for its fact-by-theory cells, climbing the ladder informal, Python runner, Lean. Use in a linglab project after facts, principles or theories are added or changed, when cells are pending, or when a cell should be firmed up; covers the linglab check, run, lean, metrics, listing and report commands."
---

# check

**Use when** facts, principles or theories were added or changed, or a cell should be firmed up.

**Read** `data/statements.json`, `data/theories.json`, `data/results.json`; `custom/registry.json` for the ladder.

**Produce** entries in `data/results.json`. The ladder of effort:
1. **Informal**: an argument or countermodel by hand, as `llm-judged` or `human` with reasons. Fast; seeds the code.
2. **Python**: `python3 utils/bin/linglab.py run [--theory T] [--fact F] [--bound N] [--force]`. The runner is model-major and resumable; a counterexample decides a claim at once; `bound` says exhaustive or first n models.
3. **Lean**: follow `utils/moves/prove.md` (statement first, countermodel first, parallel tracks, time-box), then run `python3 utils/bin/linglab.py lean`. Names: `F01` proves the claim, `F01_fail` its negation; the claim must be the fact's spec (the run lists theorems it did not credit, and why).

Other verifiers (Rocq/Coq, Isabelle, ...): implement `utils/docs/INTERFACE.md`, add the name to the ladder in `custom/registry.json`.

Other commands: `check` (validate the data), `metrics` (sizes), `listing` (rebuild Raw Facts), `report`.

**Pitfalls**
- Run `check` first. Fix structure errors before running.
- Think about loop structure before a big run: model-major, small pending set, caching, batching (sharding is not implemented yet). State the cost of a sweep.
- Skip redundant checks unless asked, but treat independent Lean and Python implementations as cross-checks. Inspect disagreements, including their model scopes.
- Never overwrite a disagreeing entry; flag it. A disagreement between kinds is information.
- Check the statement, not just the theorem name. Check no `sorry`.
- No Lean: label results `computed`, never `proved`.
- An `out_of_scope` cell is not a failure. `pending` is not a failure.
- Before reporting results, go through each fail and check that the theory's source claims to cover that fact. If it doesn't (it leaves the fact to a mechanism the theory does not include), declare `primitives` or `predicts` and `uses` and rerun. Don't report it as a fail with a caveat.
- Say why a cell is out of scope: `fragment` (cannot be stated), `no_prediction` (the theory has no linking for this kind of fact: give the theory a `predicts` list), `primitive` (a notion it does not implement, or that its source leaves to another mechanism: `primitives` on the theory, `uses` on the fact). The runner records it as `scope`.
- A sentence with several parses stays one fact; give it `parses` and let each theory choose (`parse_policy`, `picks`). Do not split the fact per reading unless the judgments differ.

**Prompt**
> Run `check`, then `run` for everything pending, then `metrics` and `report`. Tell me counts per outcome and any conflicts. For the cells that failed, check that the theory's source claims to cover the fact, then show me the countermodel in plain words.
