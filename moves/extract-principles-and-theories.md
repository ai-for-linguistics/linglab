# extract-principles-and-theories

**Use when** a paper proposes or assumes a theory, and you want it as a column.

**Read** the paper; existing principles in `data/statements.json` (reuse before adding); `data/theories.json`.

**Produce** principles (`role: "principle"`, id `P-..`) in **three layers**: `text` (plain words, with the origin quote and page), `notation` (the paper's own symbolic form as LaTeX: copy it from the paper when there is one, and say so in the origin), and code (Python chunk `# BEGIN principle:P-..` ... `# END`; Lean chunk likewise). Add relations (`stronger`, `weaker`, `related`, `incompatible`) to existing principles. Flag `auxiliary` or `vocabulary` where right. Then one theory entry listing its principles (`kind: original`, origin with page, a `description` in words, and `fragments`: the ids of the fragment(s) it is stated over). Fixes and variants: `parent` set, full principle list given.

**Fragments.** The fragment is the object language a theory is stated over (syntax, what a model is, the values, how truth, felicity and entailment are defined). Write one entry per fragment in `data/fragments.json` (`summary` in words, `defs` with words and LaTeX, `files` with the code), and say which other theories use the same one (they list the same id). A theory may use several fragments, and two theories of one paper may use different ones.

**Checks.** After writing the code, record how it was checked in the item's `checks` log: an independent plain-English reading of the code (`by: llm`, `what: readback`, with the `readback` text written WITHOUT looking at the statement's words) and its verdict against the words. Humans' checks are added later (the report can export ticks). Never overwrite a check; add one.

**Declare coverage before the first run.** List what the paper says its account does *not* cover or leaves to something else: other mechanisms (for example scalar implicatures, presupposition), other modal flavours, other constructions. Turn each item into `primitives` or `predicts` on the theory and `uses` on the affected facts (SPEC section 2). A theory that declares `primitives` must also list the notion of every fact type it handles (`entailment`, `felicity`, `truth`, ...): a type missing from the list makes all its facts out of scope. Show the user the list. A baseline or reference theory usually declares nothing, so that it is judged on every fact.

**Pitfalls**
- Principles are independent of any family; do not refuse a combination. Record incompatibilities as relations.
- Tests are not parts of a theory. Data goes in facts, never in principles.
- Two candidate principles that determine each other are one; an effect produced by several mechanisms is a result, not a principle.
- Where the paper is vague, do not choose silently: keep a note, and a Literal and a Charitable reading if it matters.
- A note on a fact or theory saying a fail "doesn't count" or "isn't modelled" means the cell is out of scope, not failed. Declare the coverage and rerun.
- Check against the page: tag balance, `linglab check` warnings (principles in no theory, missing Python ids).

**Prompt**
> Read `literature/<paper>.pdf`. Extract its assumptions as principles (reuse existing ones where they match) and add the paper's theory as a column in `data/theories.json`, with page references. Mark auxiliary and vocabulary principles. List what the paper says its account leaves out and declare it (`primitives` or `predicts` on the theory, `uses` on the facts); show me the list. Write the Python for each in tagged chunks, run `python3 utils/bin/linglab.py check` and `run`, and tell me which facts it passes.
