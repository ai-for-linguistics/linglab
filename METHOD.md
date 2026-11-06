# METHOD

For the agent, and for curious humans. About two pages. Details of the contract are in `docs/SPEC.md`.

## The model

- A **fact** (an empirical datum) and a **principle** (a theoretical assumption) are the same kind of object: a statement in words and in code, with origins (paper, page, quote), a confidence, and relations to other statements. They live in `data/statements.json`.
- A **theory** is a set of principles (`data/theories.json`). Principles do not belong to a family: any set can be tried, and a bad combination just breaks. The theory's notion of felicity or consequence is a principle too (flagged `vocabulary`). Assumptions that do not distinguish theories are flagged `auxiliary`.
- A fix is a theory with a parent. Only the changed principles need new work.
- **Raw Facts** (`RAW`) is the theory made of all the facts. It passes everything and is as large as the data. It catches facts that duplicate or contradict each other, and is the size baseline every real theory should beat.
- The space is a table: facts are rows, theories are columns. A cell holds **entries** (outcome, kind, who, when, reasons). The page pools them with a ladder: `lean > python > human > paper-claim > user-claim > llm-judged`. The strongest kind present decides the display. Disagreement at the same rank is a **conflict**; a weaker rank that disagrees adds a warning. Both are marked, never blocking.
- The goal is **compression**: coverage against size. The Coverage × Complexity tab shows the observed frontier of coverage against complexity, with a proxy pill on each axis, data filters and theory-group chips; a fold below has two proxy-against-proxy plots and a length table. Metrics disagree with each other, so the axes are choosable.

## The four activities

Labels, not steps; use them in any order. **Set up** (interview, first page). **Integrate** (facts and principles from papers). **Create** (propose and repair principles, theories, separating facts). **Exploit** (read the page, review, plan, make other views).

## Defaults, not rules

Everything can be changed by asking: fact types, kinds, metrics, ladder, plots, tabs, the whole page. Changes go in the project, never in `utils/`: `custom/registry.json` for ladder and metrics, a copy of `utils/template/report/template.html` as `report/template.html` for the page, `custom/` for other views. Do the change when asked; do not ask permission to customize.

## Guardrails (these are not defaults)

- **Status honesty.** Every result says how it was obtained. Findings use `proved` (Lean, builds, no `sorry`), `computed` (finite models, with the bound stated), `argued`, `literature`, `open`. "Not found" is about the search space: write it so. "Consistent" needs a model; "inconsistent" needs a proof.
- **Informal is never shown as formal.** An `llm-judged` or `paper-claim` entry never looks like a `lean` one. A stronger result does not overwrite a weaker one.
- **Say which fragment** a conclusion holds in, and re-check it when the fragment grows.
- **Fact statements are reviewed.** First drafts are often wrong (many were rewritten in an earlier project). Raw Facts catches duplicate or contradictory facts, not wrong translations: the user checks the translation of each statement in the Translations tab.
- **Entailment and felicity are parameters, not truths.** Papers disagree. Record the choice in `params`; mark dependent cells.
- **Out of scope, failed, pending are different.** Out of scope: the theory cannot express the fact, *or its source says the fact is handled by a mechanism the theory does not include* (record it with `uses` on the fact and `primitives` on the theory, or `predicts` for a whole type of fact). Failed: the theory covers the fact and gets it wrong. Pending: not yet tested. Never merge them. If you are about to write "a fail here means not modelled", the cell is out of scope: change the data, don't annotate it.
- **Separate soundness from adequacy**, and a paper's claim from our formalization of it ("in our formalization").
- **One folder per agent.** One Lean workspace; never two agents building in the same `.lake`.
- **Private by default; ask before publishing** anything, and say who can see it.
- Log decisions with who decided. Small commits (if git is on). Modest claims; do not rank arbitrary choices. Stop background work of low value. Show everything foldable and folded by default, with readable names.

## Compute design

Compute is the scarce resource. Before running, think about loop structure.
- Informal first (a verdict by argument is cheap and seeds the code), then Python (finds the verdict), then Lean (certifies it). Verdicts are cheap, proofs are expensive.
- The Python runner is **model-major**: build each model once, test every still-pending claim on it, and let a counterexample decide a claim at once. Keep the pending set small; cache subformula values per model; shard by model range; keep runs resumable.
- Cheap bookkeeping before expensive search. When reporting a search, say how many candidates were tested and what the alternative would have cost.
- Spend tokens knowingly. A sweep over parameters or theories multiplies cost: state the estimate first.
- A modified theory (a delta) will reuse its parent's results (planned; today every new theory recomputes its cells).

## Working with sub-agents

At most 5 in parallel, each in its own folder, each with a deliverable, a status vocabulary, a time box and a stop clause. Ask every hand-back for what was not done. Spot-check statements, not just names: an existing Lean theorem name proves nothing until its statement matches the prose. If an agent repeats its hand-back, stop it and take the first complete report. Agents summarizing agents compound errors.

## Lean

Before writing a principle, a fact or a proof in Lean, get a short guide: how to set it up, what worked before, known traps. Then have a sub-agent write and check it. Use the single workspace in `lean/`. Name theorems by the convention in SPEC section 5. Without Lean, stay in no-Lean mode.

## Reviewing a paper (seven checks, each optional)

1. Translation sheet: clause, Lean or Python, plain-English reading.
2. The paper's own worked examples reproduced.
3. An independent critic, with a fresh context, back-translates the code.
4. Typos and internal consistency; keep a Literal and a Corrected version.
5. The paper's theorems and derivations proved, refuted or redone.
6. All facts run, including failures the paper does not notice.
7. Ablation of each principle (idle ones), and comparison with the same principle in other papers.

See `moves/review-a-paper.md`.

## Twelve lessons, in their useful form

1. Use one shared `Theory` interface and one shared syntax; theories translate, and may fail.
2. Keep Raw Facts: it is the baseline and a consistency check.
3. Statement faithfulness is the main risk. Settle the interface first; it changes the meaning of many facts.
4. Entailment and felicity are theory-dependent; make them explicit parameters.
5. About a third of cells may be out of scope (plurals, modals, counting). Say so plainly.
6. Not all theories decompose into switches. Tag code chunks with the principles they cover and measure size by chunk.
7. Keep the ladder and flags; record the source of every claim, and whether a paper tested it.
8. Informal verdicts match machine verdicts nearly always; proofs cost hours. Python first, Lean second.
9. Complexity metrics disagree. Expose the choice.
10. Language was not the lever; process and scope were. Lean rebuilds fast.
11. Do not copy code between projects or hard-code names in the page. Generic rules plus exceptions kept as data.
12. The user wants: foldable and folded, readable names, short cells with detail on hover, decisions logged with who, small commits, modest claims, at most 5 agents, no low-value background work, check before answering.

## Disclaimer

Beta. Produced with AI assistance. Results may be wrong: check them (especially the translation of statements into code) before drawing scientific conclusions. Amend them by hand where needed. Iterate. Never present an AI-assisted result as established: say how it was obtained.
