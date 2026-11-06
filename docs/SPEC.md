# SPEC: the beta package (contract for all parts)

Every part of the package (Python library and CLI, Lean workspace, report, docs, slides) follows this file. If something here is wrong or missing, say so in your hand-back instead of silently diverging. Decisions and their alternatives are listed in `DECISIONS.md` (to be written from `## Decisions` below).

Model in one paragraph (see `MODEL.md`): rows are **facts**, columns are **theories** (a theory is a set of **principles**; facts and principles are both *statements in code*); a cell holds a list of **entries** (outcome + kind + reasons); the page pools them with a ladder; the objective is compression (coverage against size). Everything customizable lives in the project's `custom/`.

## 1. Layout

**The package** (this repository's root; zipped as `linglab-beta.zip`, unzips into the project's `utils/`):

```
README.md          what it is, requirements, the one prompt
BOOTSTRAP.md       the first thing the agent reads (setup interview, then work)
METHOD.md          the method in about two pages (model, guardrails, pitfalls)
GUIDE.md           for the human: screens, where to chat, how to move forward, prompt ideas
moves/             ten short playbooks (tips, not procedures)
bin/linglab.py        the one command-line tool (Python 3, standard library only)
python/linglab/       the Python library (vocabulary, runner, metrics, listing)
lean/              Lake workspace template (library Linglab: the interface only; theories go in Linglab/Theories/)
extras/agda/       optional Agda workspace template (same interface)
template/          brief.md, data/*.json (empty), custom/registry.json, report/template.html
example/           a finished toy project (presupposition projection), runnable
docs/              SPEC.md, MODEL.md, INTERFACE.md
slides/            index.html (deck), screenplay.md
```

**A project** (what the user sees; created by `linglab init` in the current folder):

```
brief.md  data/  report/  literature/  custom/  utils/  AGENTS.md  CLAUDE.md
(python/ and lean/ appear when first used)
```
`AGENTS.md` and `CLAUDE.md` are identical two-line pointers: "This is a linglab project. Read utils/BOOTSTRAP.md, then utils/METHOD.md, and follow them." (Any agent started in the folder then finds its instructions.)

Commands run from the project root: `python3 utils/bin/linglab.py <command>`. In `example/`, `python3 ../bin/linglab.py <command>`. `linglab.py` locates the toolkit from its own path and operates on the current directory as the project.

## 2. Data files (all JSON, UTF-8, human-editable, indent 2)

### data/meta.json
`{title, question, scope, suggestions[], goals[], papers[{id,title,role(target|data|proposal|background),have(bool),note}], params[{id,name,options[],chosen,note}], takeaways[{text,status,link}], limits[], updated}` — all optional except `title`. `params` are setup choices that affect meaning (consequence relation, a reading choice); cells may name the param they depend on.

### data/statements.json  (facts and principles, one list)
```
{ "id": "F01", "role": "fact" | "principle",
  "name": "short readable name", "text": "the statement in words",
  "confidence": 0..1, "origins": [{"source": "paper id or 'user'", "page": "", "quote": ""}],
  "relations": [{"rel": "stronger|weaker|related|incompatible", "to": "id", "note": ""}],
  "code": {"python": "<principle id or null>", "lean": "<Lean name or null>"},
  "notes": "" ,
  "notation": "LaTeX, optional: the paper-style symbolic form (principles: copied from the paper when it has one; facts: absent = generated, see below)",
  "checks": [ {"by":"llm|human|other", "who":"", "when":"YYYY-MM-DD", "what":"readback|translation|example|other",
               "verdict":"agrees|disagrees|partial|unclear", "readback":"plain-English reading of the CODE, written without looking at the statement's words (what=readback)", "note":"", "ref":""} ],
  // facts only:
  "type": "entailment|felicity|truth|preference|consistency|property|other",
  "expected": "holds" | "fails",          // default holds
  "context": "null",                      // default
  "spec": { ... },                        // by type, see below; absent for type other
  "group": "G-comm",                      // optional: facts forming a cluster
  "about": "language" | "system",         // default language
  "contested": false,
  "kind": "free string",                   // optional: kind of fact, groups the heatmap columns (default: type)
  "layer": "free string",                 // optional: reliability set (default: contested | uncontested)
  "parses": [{"id":"wide","label":"words","spec":{...}}],  // optional: other parses of the sentence (same shape as `spec`); `spec` is the parse "main"
  "uses": ["alternatives"],               // optional: notions the fact needs (a theory that declares `primitives` without them is out of scope: primitive)
  // principles only:
  "auxiliary": false, "vocabulary": false }
```
Ids: facts `F..`, principles `P-..`. Ids are unique across the file.

**Shared syntax** (JSON s-expressions, version 2; full table in INTERFACE.md section 1): an atom is a string (`"p"`); a predicate application is `["Student","?x"]` (a head that is not reserved, then terms: constants are plain strings, variables start with `?`); connectives `["not",A]`, `["and",A,B]`, `["or",A,B]`, `["if",A,B]`, `["iff",A,B]`; generalized quantifiers `["some","?x",R,S]`, `["every","?x",R,S]`, `["no","?x",R,S]` (restrictor R, scope S; the list of binders is open, a theory may register `most`); first-order `["exists","?x",A]`, `["forall","?x",A]`; modals `["must",A]`, `["may",A]` (flavour left to the theory). Any other head is a theory-defined operator (`["exh",A]`). Variables must be bound. A discourse is a list of sentences. Version 1 facts remain valid. A theory that does not define a head, predicate or atom cannot translate the sentence: out of scope; `linglab check` warns when no principle of the project defines an operator or predicate a fact uses.

**Fact specs by type** (all over the shared syntax):
- `entailment`: `{"premises":[S...], "conclusion": S}` — claim: in every model, if the premises hold (the theory's entailment notion), the conclusion holds. Empty premises = validity.
- `felicity`: `{"discourse":[S...]}` — claim: the discourse is felicitous (theory's notion) in the null context.
- `consistency`: `{"premises":[S...]}` — claim: there is a model where all premises are true.
- `truth`: `{"sentence": S, "relation": "equals"|"within"|"includes", "target": S}` — the truth set of `sentence` equals / is within / includes the truth set of `target`.
- `preference`: `{"sentence": S, "preferred": S, "over": S}` — declared; the beta runner does not implement it and returns `pending` (shows the pending state).
- `property`: `{"check": "<name of a property registered in the project's python/>"}` — about the system.
- `other`: no spec; results come from entries of kind `human`, `paper-claim`, `user-claim`, `llm-judged`.
Equivalence is two grouped entailment facts (same `group`).

`checks` is a log: several entries per item (a human may check several times; LLM and human are both recorded). A check never changes an outcome; it records whether the words, the notation and the code say the same thing.

### data/fragments.json  (optional file; missing = `[]`)
A fragment is the object language a theory is stated over (syntax, models, values, notions), shared by theories.
`[{ "id": "FR-TOY", "name": "", "summary": "words", "notation": "LaTeX of the definitions", "defs": [{"label":"models","text":"words","notation":"LaTeX"}], "files": {"python":["python/principles.py"], "lean":["lean/Linglab/..."], "agda":[]}, "checks": [same entries as above], "notes": "" }]`

### data/theories.json
`[{ "id": "T-MK", "name": "Middle Kleene", "description": "words (a summary)", "notation": "LaTeX, optional", "fragments": ["FR-TOY"] (ids; several allowed, a fragment may be shared), "principles": ["P-NEG","P-AND-MK",...], "parent": null | "T-MK" (delta: `principles` lists the full resulting set, `parent` is informational), "kind": "original|fix|creative|reference", "origin": {"source":"","page":""}, "family": "", "short": "", "generated": null | "listing", "notes": ""}]`
`family` (free text) groups the heatmap rows when the project has two or more families; `short` is an optional display name (heatmap, plots, chips; the full `name` stays in titles and cards); `kind` also groups the chips of Coverage vs Complexity when there are no families.
Optional fields that say what the theory does with a fact (all absent = no restriction, the previous behaviour): `predicts` (fact types it makes predictions for; others are out of scope, reason `no_prediction`), `primitives` (notions it implements, for example `entailment`, `felicity`, `truth`, `alternatives`; a fact of a type or `uses` outside the list is out of scope, reason `primitive`; this is also how to record a fact that the theory's source leaves to a mechanism the theory does not include, such as scalar implicatures in a logic of free choice: a cell like that is out of scope, never a fail), `parse_policy` (`first` default: only the fact's own spec; `any`: pass if some parse passes; `all`: pass iff every parse passes) and `picks` (`{fact id: [parse ids]}`: the parses this theory uses for a fact). Which parse a theory takes is the theory's choice, not the fact's: the fact keeps the sentence and the judgment.
A theory with `generated: "listing"` is Raw Facts (id `RAW`): built by `linglab listing` from the facts.

**Inlined data** (`linglab report`): keys `meta, statements, theories, results, findings, metrics, registry, code, fragments, fragment_users`. `fragment_users` is derived: `{fragment id: [theory ids]}`. `code.facts[id]` has `spec_text` (plain) and `notation_auto` (LaTeX generated from the spec; the fact's own `notation` wins when present). Conventions of `notation_auto` are in the docstring of `python/linglab/latex.py` (entailment `\vDash`/`\nvDash`, felicity `\mathrm{felic}(d)` or `\neg\,\mathrm{felic}(d)` when expected fails, quantifiers `\mathrm{some}\,x\,(R)\,(S)`). KaTeX (`template/report/vendor/katex/`, see `THIRD_PARTY.md`) is inlined at the template's `/*__KATEX_CSS__*/` and `/*__KATEX_JS__*/` placeholders only if some statement, fragment or theory has `notation` or a fact has `notation_auto`; otherwise both become empty.

### Display options of the report (all optional; nothing is hardcoded to one project)
- `data/meta.json`: `short_names` {theory id: short name} (alternative to `short` on the theory), `family_short` {family: short family name}, `fact_kinds` {kind: title}, `theory_kinds` {theory kind: row label, default original = Source, fix = Modified, creative = New}, `page_title` (default "linglab: benchmarking and constructing theories with AI and verifiers"), `subtitle` (plain string; default "Proof of concept related to <paper title> (authors, year)" built from `paper`, else from the first of `papers` with role target, else `title`), `paper` {title, authors, year, url}, and the warning band: `banner` (the key sentence, bold; `""` hides the whole band), `banner_title` (the tracked line above it), `banner_points` (list of caveats in small type); absent = the default beta warning.
- `custom/registry.json`: `layers` (list of ids or `{id, name}`: order and names of the reliability sets), `proof_kinds` (kinds of the ladder drawn with the proof dot; default `["lean","agda"]`).
- Optional on facts: `requires` (a fragment id or a list: the fragment the fact needs; shown in the panel with whether the theory declares it).
- Fallbacks: fewer than two families = flat rows; rows of a family are labelled by the kind of theory (Source / Modified ...) when it is unique in the family, else by the short name; no `kind` on facts = grouped by `type`; no `layer` = contested / uncontested; no `short` = full name. `linglab check` validates the types of these fields.

### data/results.json  (entries; many per cell)
`[{ "fact": "F01", "theory": "T-MK", "outcome": "pass|fail|pending|out_of_scope", "kind": "lean|agda|python|human|paper-claim|user-claim|llm-judged", "who": "runner|name", "when": "YYYY-MM-DD", "reasons": "free text (a countermodel, a quote, an argument)", "ref": "file or name of the code/proof/source", "bound": "exhaustive | first n models | ''", "digest": "set by the runner: a hash of the inputs, so changed cells are recomputed", "presence": "in source|mentioned not tested|mentioned disregarded|not mentioned" (paper-claim only), "outside_fragment": false, "depends_on": "param id" | "", "note": "" }]`
Optional entry fields: `scope` (on an `out_of_scope` entry, why: `fragment` the sentence cannot be stated in the theory, `no_prediction` the theory has no linking for this kind of fact, `primitive` the fact uses a notion the theory does not implement, including one its source leaves to another mechanism) and `parses` (`{parse id: outcome}`, when several parses of the sentence were evaluated).
`pass` means the fact's expected outcome was met (an expected-`fails` fact passes when the claim fails). Re-running a checker replaces that checker's previous entries for the cell (same fact, theory, kind, who) and never touches other kinds.

### data/readings.json  (optional; an explanation of a cell, never evidence)
`[{ "fact": "F01", "theory": "T-SK", "text": "how the proof or the run seems to have worked", "by": "assistant|name", "when": "YYYY-MM-DD", "review": "unreviewed|accepted|corrected", "reviewer": "name (when reviewed)" }]`. At most one reading per (fact, theory). A reading is the meta-reading of what happened in a cell, written by an assistant or a person. It is **not** an entry: it is never pooled, never counted, never plotted, and never changes a verdict. The report shows it as the fourth folded part of the cell panel, labelled "not evidence". `linglab check` validates the references and the `review` value.

### data/findings.json  (general results and take-home messages)
`[{ "id":"R1","title":"","text":"","status":"proved|computed|argued|literature|open","basis":"lean|python|…","principles":[ids],"facts":[ids],"evidence":"","note":"" }]` e.g. "every theory with P-AND-WK and P-FELIC-DEF fails F01".

### data/metrics.json  (generated by `linglab metrics`; never edited)
`{"theories": {"T-MK": {"principles": {"P-AND-MK": {"python": {"chars":N,"words":N,"lines":N,"gzip":N}, "lean": {...}}}, "total": {"python":{...},"lean":{...}}, "n_principles": N, "n_principles_no_aux": N}}, "raw": {...same shape for RAW...}}`
Sizes are measured on tagged chunks with comments and blank lines stripped. Missing language = absent key.

### custom/registry.json  (defaults ship in template/; the project copy wins)
`{"ladder": ["lean","agda","python","human","paper-claim","user-claim","llm-judged"], "outcomes": [...], "fact_types": [...], "coverage_metrics": [{"id":"passed","name":"...","note":""}], "size_metrics": [...]}`
The ladder is strongest first. The report implements the named metrics in JS; unknown names are shown disabled. New metrics are added by prompting: the registry lists them and the report code implements them (the agent edits a project copy of `report/template.html`).

## 3. Pooling (report and `linglab` use the same rule)
For a cell, take its entries. Displayed outcome = the outcome of the strongest ladder rank that has an entry (entries with `pending` do not count unless nothing else exists). If entries at that rank disagree on pass/fail: `conflict` (marked, never blocking). A weaker rank that disagrees with the displayed outcome adds a warning marker. `out_of_scope` is displayed as such and excluded from "applicable". No entries: `pending`. Coverage metrics: `passed` = number of facts with displayed pass; `passed_over_applicable`; `confidence_weighted`; each with switches: include/exclude `llm-judged`, include/exclude `about:system` facts, exclude contested.

## 4. Python library and CLI (`python/linglab/`, stdlib only)

`bin/linglab.py` subcommands:
- `init <Name> [--git]`: create the project files in the cwd (brief.md, data/ from template, report/, literature/, custom/registry.json, AGENTS.md, CLAUDE.md, .gitignore); refuse if brief.md exists.
- `check`: validate the data files (structure, unique ids, references to existing ids, enums, spec fields by type, ladder kinds known); print problems with file and id; exit 1 on errors. Warnings: facts with no confidence; principles referenced by no theory; Python principle ids missing from `python/`.
- `run [--theory T] [--fact F] [--bound N] [--force]`: run the Python checker (below) for pending or all cells, write entries to `data/results.json`, then run `metrics`.
- `lean [--init] [--build-only]`: `--init` copies the interface-only Lean workspace to `lean/` (once); `--init --linglib` overlays linglib mode (`extras/linglib`: a lakefile requiring linglib at a tag, linglib's Lean version, a worked adapter; nothing is downloaded, `linglab lean` then refuses to build until the packages are fetched). Otherwise: if `lake` exists and `lean/` exists: `lake build` in `lean/`, then for each (theory, fact) detect Lean theorems by the naming convention (section 5) and write `lean` entries (`pass` for `T_<theory>.<fact>`, `fail` for `.._fail` proving the negation); report build errors. If no Lean: print how to install, exit 0.
- `metrics`: write `data/metrics.json` from chunk markers.
- `listing`: (re)build Raw Facts: `data/theories.json` entry `RAW`, and its python results (all facts `pass`, kind `python`, reasons `listed`); report contradictory facts (same normalized spec, opposite expected) as errors.
- `report [-o out.html]`: write `report/index.html` (inline `meta, statements, theories, results, findings, metrics, registry` into `report/template.html` if the project has one, else the toolkit template).
- `agda [--init] [--build-only]`: the same for the optional Agda workspace (`extras/agda`), entries of kind `agda`.
- `zip`: (toolkit only) write `dist/linglab-beta.zip` of the package. `site`: (toolkit only) write `dist/site/`, the slides with the zip next to them.
- `new-fact`, `new-principle`, `new-theory` helpers are NOT in the beta (the agent edits JSON).

**Vocabulary and theory API (`linglab.vocab`)**
- `Theory`: attributes `id`, `name`; method `translate(s) -> formula | None` (None = not expressible: the cell is `out_of_scope`); `models(bound)` iterator of models (deterministic order, smallest first); `true_in(m, f)`, `defined_in(m, f)`; vocabulary primitives with defaults: `ent_ok(m, prem_formulas, concl_formula)`, `felic_ok(m, disc_formulas)`, `cons_ok(m, prem_formulas)`. Theories are *built from principles* (a principle may also register `b.operator(op, fn, arity)` for operators that see formulas and other models, override `true_in` and `defined_in`, set `describe_model`, and share data through `b.data`): `Principle(id, apply)` where `apply(builder)` may register connectives (`builder.connective("and", fn)`), set model constraints (`builder.constrain(fn)`), and override vocabulary primitives (`builder.set("ent_ok", fn)`, `"felic_ok"`). A theory = ordered list of principle ids applied in order (later overrides earlier). Missing connective ⇒ `translate` returns None for sentences using it. Principles are independent of theories: a wrong combination breaks or underperforms, it is not refused.
- Principles live in the project's `python/principles.py` (the example's is `example/python/principles.py`), each in a chunk: `# BEGIN principle:P-AND-MK` ... `# END principle:P-AND-MK`, registered with `@principle("P-AND-MK")`.
- **Claims** (from a fact spec + theory): `Claim(kind="forall"|"exists", pred(model)->bool)`. entailment/felicity/truth: forall; consistency: exists. Fact outcome: `raw = (forall: no violation found | exists: witness found)`; `pass = (raw == (expected=="holds"))`.
- **Model-major runner** (`linglab.runner`): for each theory, build claims for all pending facts (translation failure ⇒ `out_of_scope` immediately, unsupported type ⇒ `pending`); then loop over models once, evaluating all still-undecided claims on each model; a violation (forall) or witness (exists) decides the claim at once, with the model as `reasons`; after the models are exhausted, the rest are decided by default and `bound` says `exhaustive` or `first n models`. Per-model memoization of subformula values. The loop order is documented in the code as a design choice (compute is the scarce resource; the agent is told to think about loop structure and sharding).
- Everything is deterministic and resumable (results are keyed per cell).

## 5. Lean workspace (`lean/`, Lake project, Lean 4.34.1, no Mathlib)

One Lake project, no copies. Library `Linglab`:
- `Linglab/Syntax.lean`: `inductive S | atom (n : String) | not (a : S) | and (a b : S) | or (a b : S) | imp (a b : S)` (shared syntax); discourse = `List S`.
- `Linglab/Theory.lean`: `structure Theory` with a model type, `translate : S → Option F`-like fields as needed (design them well; the toy fragment must be implementable and `decide`-able), `trueIn`, `definedIn`, and the vocabulary `Ent`, `Felic`, `Cons` as Props over models; claim shapes `Holds`, `Fails` (negation), with `Expr` expressed by `translate` returning `none` (out of scope, not provable either way).
- `Linglab/Toy/*.lean`: the toy presupposition fragment, one file per theory (`T_SK`, `T_WK`, `T_MK`, `T_MK_some`), each with `-- BEGIN principle:P-...` / `-- END principle:P-...` chunks around the Lean code of each principle, then theorems.
- **Naming convention for results:** `namespace T_MK` ... `theorem F01 : <claim holds> := by decide` (outcome `pass` when the fact is expected to hold and the theorem proves the claim, or expected to fail and the theorem `F02_fail` proves the negation; i.e. `F..` = the *claim* is proved, `F.._fail` = the claim's negation is proved; `linglab lean` combines with the fact's `expected`). Raw Facts in Lean: `Linglab/Toy/Raw.lean` lists the claims and proves each by membership.
- A `lean/README.md` explains in 10 lines how to add a theory and a fact.

## 6. The toy fragment (example/ project: "Presupposition projection, toy")

Models: valuations of `s`, `p`, `q` in {0,1} and `a` in {1,0} when `s`=1 and `a`=# (undefined) when `s`=0 (`a` is "the king is bald", `s` is "there is a king"). Values: 1, 0, #. Sizes: 12 models.
Principles (python and lean chunks): `P-NEG` (¬: swaps 1/0, # stays), `P-AND-SK`, `P-AND-WK`, `P-AND-MK`, `P-OR-SK`, `P-OR-WK`, `P-OR-MK`, `P-ENT-T` (premises all 1 ⇒ conclusion 1), `P-FELIC-DEF` (felicitous iff defined in every model), `P-FELIC-SOME` (felicitous iff defined in some model; relations: incompatible with `P-FELIC-DEF`), `P-AUX-PRESUP` (auxiliary: the model constraint a=# iff s=0). Connectives: SK = strong Kleene (and: 0 if either 0, 1 if both 1, else #; or dual); WK = weak Kleene (# if either #, else classical); MK = middle Kleene, left to right (and: left 0 ⇒ 0; left # ⇒ #; left 1 ⇒ right; or: left 1 ⇒ 1; left # ⇒ #; left 0 ⇒ right).
Theories: `T-SK` {NEG, AND-SK, OR-SK, ENT-T, FELIC-DEF, AUX-PRESUP}; `T-WK` {NEG, AND-WK, ENT-T, FELIC-DEF, AUX-PRESUP} (no disjunction: facts with `or` are out of scope); `T-MK` {NEG, AND-MK, OR-MK, ENT-T, FELIC-DEF, AUX-PRESUP}; `T-MK-some` (fix, parent `T-MK`, FELIC-DEF replaced by FELIC-SOME); `RAW`.
Facts (ids fixed; `expected` as given; judgments from the standard presupposition-filtering data):
- F01 felicity `["s","a"]`-as-one-sentence: discourse `[["and","s","a"]]`, holds ("There is a king and the king is bald")
- F02 felicity `[["and","a","s"]]`, fails (order asymmetry)
- F03 felicity `["a"]`, fails (bare trigger)
- F04 felicity `[["or",["not","s"],"a"]]`, holds ("Either there is no king or the king is bald")
- F05a entailment p∧q ⊨ q∧p, F05b q∧p ⊨ p∧q (group `G-comm`), holds
- F06 entailment p ⊨ p∧q, fails (non-entailment)
- F07 entailment ⊨ a∨¬a (no premises), fails (excluded middle fails with a presupposition)
- F08 consistency `[s, ["not","s"]]`, fails
- F09 truth sentence `["and","s","a"]` equals target `a`, holds
- F10 other: "Speakers find 'a and s' worse than 's and a' (graded judgment)": no spec; entries by human/paper-claim only; contested true, confidence 0.6
- F11 preference: sentence `["and","s","a"]` preferred `a` over `s`... any well-formed preference spec; pending in beta
Expected python outcomes to assert in tests: F01: SK pass, MK pass, WK fail, MK-some pass; F02: SK fail, MK pass, WK pass, MK-some pass? (compute and verify: under FELIC-SOME, a∧s is defined in some model so felicitous ⇒ expected fails ⇒ fail); F03: SK/WK/MK pass, MK-some fail (a is defined in some model); F04: SK pass, MK pass, WK out_of_scope, MK-some pass; F07: SK/MK pass, WK out_of_scope; F05a/b, F06, F08, F09: pass in all theories with the required connectives. The example data also contains hand-written entries: a `paper-claim` pair that conflicts on (F10? no: use F01, T-WK: paper A pass, paper B fail, rank paper-claim only if no formal entry — so create the conflict on a cell with no python/lean entry: (F10, T-MK): two `paper-claim` entries disagreeing), a `human` entry (F10, T-MK pass, outside_fragment), an `llm-judged` entry that disagrees with python (warning marker) on (F02, T-SK), and a `python` entry for T-MK and a `lean` entry that disagree is NOT created (formal entries must be honest).

## 7. Report (`template/report/template.html`, vanilla JS, one file, no network, light mode only, phone-friendly)
Data inlined at `/*__DATA__*/null`. URL hash selects tab. Everything foldable and folded by default; names readable; short cells with detail on hover/click.
Page: a warning band (tracked title line that scrolls away; key sentence and caveats sticky at the top), the title and subtitle, then the tabs, sticky below the band. Tabs, in this order and without icons: Overview, Empirical Space, Theoretical Space, Theories × Facts, Coverage × Complexity, then the toolkit's own Translations, Findings and Instructions (key `guide`). Every in-page navigation is a history entry; the back button restores the tab and the scroll position; any navigation closes the docked panel. **Overview** (three piles that sit side by side when there is room and stack otherwise: the facts × theories × verifiers figure, the coverage × complexity figure (both from the slides, in equal square frames, each a link to its tab) and the text with question, scope, params, papers with PDF status, an origin table of the theories (full citation with link for theories from a paper, the parent's short code for derived ones), counts, take-home messages, winners by metric; limits and disclaimers as plain text under the piles); **Empirical space** (foldable cards per fact: statement, type, expected, context, how it is tested, what pass/fail mean, quotes/origins/confidence, contested, code links, group, and a row of its results per theory as chips; filter/search; groups shown as one expandable item); **Theoretical space** (foldable cards per principle: statement, quotes, relations clickable, auxiliary/vocabulary badges, code size; theories listed with their principle bundle; the theory cards are its last block); **Theories × Facts** (heatmap, one square per cell, colour = pooled outcome; marks: dot = proof kind (lean, agda), stripes = informal evidence, cross = conflict or warning, yellow cross and paler = controversial fact (the field is `contested`); theories as rows grouped by family when there are two or more (rows labelled Source / Modified / ... by kind of theory, else by short name), facts as columns grouped by kind with a small gap between kinds, controversial facts last within a kind; Raw Facts last as the baseline; toggle Theories × Facts | Facts × Theories; sticky headers; legend in three clusters above the table (wide) or beside it (long); bars clickable for the summary by reliability set and by kind of evidence; click a square for a docked panel folded in three parts: 1. Fact, 2. Principles involved (experimental: principles of the bundle linked to the fact by relations or findings, else the whole bundle, plus the fragment the fact requires and the theory's fragments), 3. Current test (verdict, kind, conflict, all entries, the Lean/Agda statements of the theory's family, how it is tested); hover shows the entries; Esc, the same square or any navigation closes the panel); **Translations** (words next to code for every principle and fact, with a tick per row kept in the browser; the one thing nobody certifies automatically); **Theory cards** (the last block of Theoretical Space, not a tab; `#cards`, `#cards:ID` and the old `#audits` open it; omitted when there is no theory; replaces Audits: per theory the summary, notation, its fragments (with 'also used by ...'), principle bundle as clickable names, auxiliary assumptions, pass/fail table, problems = failed facts with countermodel text folded; fragments show their definitions, files and check log); **Coverage × Complexity** (replaces Explorer; `#explorer` still routes here): left box with the text, data filters (evidence, system facts, contested, reliability set, kind of fact) and theory-group chips (families, else kinds of theory; Raw Facts is the baseline); axes-only square plot sized from the viewport, "best" arrow, observed frontier, one proxy pill on each axis (proxies from `custom/registry.json`: `coverage_metrics`, `size_metrics`); sticky left column; below, a fold with Complexity x Complexity, Coverage x Coverage and the length table; **Findings** (list with filters); **Instructions** (subtabs: Guide, with how to arrange screens, how to move forward, prompt ideas with copy buttons, how to ask for changes to the page and the glossary of statuses; Method and Technical contract, rendered at build time from `METHOD.md` and `docs/SPEC.md` into the data as `docs`). Ask buttons (copy-prompt) on cards and cells.

## 8. Decisions (summary)
D01 rewrite on a branch; D02 package = repo root, zipped, unzips to `utils/`; D03 one CLI `linglab.py`, stdlib only; D04 JSON data, no database; D05 two authored files (statements, theories), results as entries; D06 pooled ladder `lean>python>human>paper-claim>user-claim>llm-judged`, conflicts marked not blocking; D07 principles independent of family; vocabulary choices are principles; D08 expressibility = `translate` returns None = out of scope; D09 Python runner model-major with pending set; D10 Lean: one Lake workspace, `decide`-style toy, naming convention for results; D11 report is one vanilla-JS file, copyable to the project for customization; D12 AGENTS.md and CLAUDE.md pointer files in the project root; D13 no skills folder: playbooks are plain markdown `moves/`; D14 no JSON-schema files: `linglab check` validates; D15 recommended setup: VS Code, report in a browser window beside the chat; D16 the beta is validated on one toy fragment, not on Anaphora.


**Look and history (report).** Palette and type of the linglab slides (navy ink, blue accent, tracked kicker labels, calm amber band, no italics); disclaimers are plain text under a highlighted heading in the Overview; the browser back button restores the tab and the scroll position (state stored with `replaceState` before an in-page link). Supersedes D34 (see DECISIONS D35).
