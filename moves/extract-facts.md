# extract-facts

**Use when** a paper (target, data or background) contains judgments, examples or claims about data.

**Read** the paper in `literature/`; `data/statements.json` (avoid duplicates); `data/meta.json` for the paper id; SPEC section 2 for fact types.

**Produce** facts in `data/statements.json` (`role: "fact"`, id `F..`): a short readable `name`, the statement in words, `type` and `spec` over the shared syntax (the symbolic form is generated from the spec; add an explicit `notation` in LaTeX when the paper has its own, e.g. a logical form), `expected` (holds or fails), `confidence`, `origins` (paper id, page, quote), `contested` if the judgment is disputed. Group minimal pairs with `group`. Worked examples of the paper become facts. Record in `checks` an independent reading of the spec back into plain English and whether it agrees with the words. Then run `check`, `listing`, `report`.

**Pitfalls**
- Hand-drafted statements are often wrong. Read each one back in plain words to the user.
- Entailment without felicity, or a premise that is vacuous (an unbound pronoun), changes the meaning. Check.
- Do not turn a blurry judgment into a hard fact: lower the confidence, mark it contested.
- Extract from every source paper, not only the first. Record where each fact comes from; mark your own as `user` or yours.
- A theory claim in a paper is not data. Keep it as `paper-claim`, not as a fact.
- A negative fact needs a translation that can succeed; otherwise it holds vacuously (the cell is out of scope).

**Prompt**
> Read `literature/<paper>.pdf` and extract its data as facts into `data/statements.json`. Give each a readable name, the statement in words, expected outcome, confidence, and page and quote. Use `other` for what has no spec. Show me the list in plain words before running anything, then run `python3 utils/bin/linglab.py check` and rebuild the report.
