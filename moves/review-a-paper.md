# review-a-paper

**Use when** the user wants to know whether a paper's theory is as claimed, in our formalization.

**Read** the paper; the theory's principles and code; the facts it was run on.

**Produce** in `reviews/<paper-id>/` (not `data/`) plus entries and findings:
1. **Translation sheet**: one row per clause: the paper's wording (page) | its symbols (the paper's formula, as `notation`) | code name | plain-English reading | Literal vs Corrected difference. The readings and verdicts also go into the `checks` log of each principle or fact (by llm or human, with who and when), so the Translations tab and the theory cards show them.
2. **Worked examples**: every example the paper computes by hand, reproduced as a fact (a mismatch is the paper's error or ours: decide which).
3. **Independent critic**: a fresh agent gets only the paper and the code, not the sheet; it back-translates the code and lists mismatches, weakenings, vacuous hypotheses. Reconcile each point and log the critic's reading as a `checks` entry (`by: llm`, `what: readback`). Without sub-agents, do an adversarial second reading yourself.
4. **Typos and internal consistency**: keep a Literal and a Corrected version, state the differences.
5. **Theorems and derivations**: restate the paper's theorems, prove or refute each; redo derivations step by step. A refutation is a finding.
6. **All facts run**, including failures the paper does not notice; for each failure give the countermodel in plain words.
7. **Ablation** of each principle (idle ones), and comparison with the same principles in other papers.

Add findings with honest status to `data/findings.json`.

**Pitfalls**
- Weakening the paper's definitions to make tests pass.
- Proving a theorem about another fragment than the claim.
- Mixing the paper's claim with our result: write "in our formalization".
- Giving a formal object (model, derivation) so the author can check a criticism.
- Fix a problem, then re-run every fact.

**Prompt**
> Review `<paper>`: translation sheet, its worked examples, an independent critic, a Literal and a Corrected version, its theorems, all facts including failures it does not notice, and an ablation of its principles. Put the sheets in `reviews/<paper>/` and the findings on the page, with honest status labels.
