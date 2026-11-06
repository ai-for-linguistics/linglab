# MODEL: facts and principles are code, a theory is a set of them, a result is a run

Status: the current model of the package; sections marked "proposed" are design notes, not implemented.

**Defaults, not rules.** This is a starting framework. By prompting, the user can change anything: test types, evidence kinds, metrics, plots, tabs, the ladder, the vocabulary, the whole report. What can change lives in small named places in the project (`custom/`), never in the downloaded toolkit. The only fixed guardrails are about honesty: every result says how it was obtained, informal is never shown as formal.

## One kind of object: a statement in code

A **fact** (an empirical datum) and a **principle** (a theoretical assumption) are the same kind of object: a statement with code (Lean and/or Python), quotes, one or several origins, a confidence, and relations to other statements (stronger / weaker / related). Facts come from data, principles from theories; that is the only difference.

- **Theory:** a set of principles (applied in a stated order: a later principle may override an earlier one), each on or off (no separate "dimensions" and "levels"). Plus a description and open metadata (origin, framework family, original / fix / creative, ...). Assumptions a theory needs but that do not distinguish it are principles flagged `auxiliary`.
- **Principles are independent of any family.** Any principle can be switched on in any theory; a wrong combination just breaks or gives a poor theory. Incompatibilities are recorded as results (which principles, which facts gained or lost), not enforced. A principle's code is a tagged chunk of the theory's code (`covers: principle id`), so size can be measured per principle.
- **The theory's implementation of the vocabulary is made of principles too** (its notion of felicity, its consequence relation, flagged `role: vocabulary`), so choosing among them is the same kind of choice as any other.
- **Fixes and variants are deltas** over a parent theory (principles added, removed, replaced), so that unchanged parts can be recycled (planned: today a new theory recomputes its cells).
- **Raw Facts:** the theory made of all the facts. It is a column like any other, and a reference point: maximal coverage, maximal complexity. It catches facts that duplicate or contradict each other (the same claim with opposite expectations); it does not check translations: that is the job of the Translations tab. Its point on the complexity plot is the baseline every real theory should beat.
- Later: principles can prove other principles, to compare theories or reduce them.

## The space

A matrix: **rows are facts, columns are theories** (Raw Facts included). A cell is what we know about one fact against one theory. Two operations add to the space: add a fact, add a principle or theory. Everything else is reading the matrix.

## Shared vocabulary, theory-specific implementations

Facts are written over a small shared vocabulary of primitives: readings (truth sets), entailment, felicity, preference, consistency, ... (the list is open), over a shared syntax of discourses. **Each theory supplies its own implementation of the primitives** (through its vocabulary principles) and a translation of the shared syntax into its own formulas; facts stay framework-neutral. A new framework is a new implementation of the vocabulary, not new facts. The vocabulary is what makes a Lean encoding of a theory testable, so the `Theory` interface is designed carefully first, drawing on the Agda `Theory` record, the Lean projects and linglib (changing it later changes the meaning of many facts).

- **Expressibility:** if a theory cannot translate a fact's discourse, the cell is `out of scope` (distinct from `failed` and from `pending`). No expressibility conjunct is written into fact statements; the translation failing is the signal, and it also stops "not derived" from holding vacuously.
- **Equivalence** is two entailments (one fact group). There is no separate same-readings primitive.
- Facts are generated from a specification and reviewed (the reviewable statement, a decision log of who decided what); first-draft statements are often wrong (many were rewritten in the Anaphora project), so every fact is validated by Raw Facts before use.

Fact types (starting list, open; new types need new primitives): truth (equals, is within, includes a target reading), entailment, felicity, preference, consistency, property (about the system, `about: system`), other (no code; the result rests on reports). Expected outcome (holds or fails) and context (default: null) are part of a fact. Equivalence is two entailments grouped as one fact; related facts (minimal pairs) can form a group; results roll up.

Facts are neutral over the shared syntax, not over everything: some need a construct a theory must interpret (plurals, modals, counting, exhaustification), added as extension modules in batches. When a setup choice is needed (for example the consequence relation, or a reading such as weak or strong donkey), the agent lists the options with a default; the choice is attached to the affected cells ("depends on the consequence relation"); the user can diverge or ask to explore several (sweeps cost tokens, and the agent says so). At setup and when a theory is added, the agent proposes checking whether linglib already has what is needed.

## Facts, probes and linking hypotheses (proposed; design note)

**Two layers.** A *behavioural* layer says what people do or say; a *theory-internal* layer says what a theory posits (a presupposition, an implicature, a "co-supposition"). Facts live in the behavioural layer, so they stay neutral between theories. A theory connects its internal notions to behaviour through a **linking hypothesis**. The adapter of a theory *is* its linking hypothesis (plus, optionally, a parser).

**Probes.** A fact is an observation of a small, extensible set of probe types, each with graded and labelled responses:

| probe | takes | response (examples) |
|---|---|---|
| judgment | a sentence, optionally in a context | acceptable, odd, false, "acceptable but funny", a rating |
| inference | premise(s), conclusion | follows / does not follow, an endorsement rate |
| comparison | two sentences | A more acceptable than B |
| scenario | a sentence and a situation | true, false, neither |
| preference | alternatives | which one is chosen |

Tests such as "hey, wait a minute" are *judgment* probes with a specific response label; the linking hypothesis says when a theory predicts that label (for example: when there is a presupposition, which is a theoretical notion).

**Text or pivot.** A fact always carries its **text** (sentence, judgment, source, context). It may also carry one or several **pivot specs**: formulas in the shared syntax. An ambiguous sentence has one spec per reading, each with an id. A theory declares what it **reads**:
- the pivot spec (it then translates it into its own forms), or
- the text (it then brings its own parser). The parser is part of the theory: principles about structure, switched on or off like any other. A theory that assigns a different structure gets its predictions through that structure.

**Several reasons for "out of scope"** (implemented in the Python runner; see INTERFACE section 10). An out-of-scope cell says why:
1. *fragment*: the sentence is not expressible or parsable in the theory;
2. *no prediction*: the theory has no linking hypothesis for this probe or response (its notion is not there);
3. *primitive*: the fact uses a primitive the theory does not implement. This includes a fact the theory's source says is handled by a mechanism the theory does not include (scalar implicatures in a logic of free choice, say): it is out of scope, not failed, even though the sentence can be expressed.
None of them is a failure: *failed* means the theory covers the fact and gets it wrong. Untested stays *pending*.

**Vocabulary grows by proposal.** The primitives (entails, presupposes, more felicitous than, ...) form a small versioned core. A theory may introduce a new one by *proposal* (name, definition, example, who proposed it, relations to others: stronger, weaker, related). Facts that use it are out of scope (primitive) for theories that do not implement it. A compatibility table in the shared index lists which theories implement which primitives.

**Portability.** The result entries of a cell are the format of a test's output. Making them portable between projects is useful; recomputing or partly reusing them is acceptable.

## A result is a list of entries

Each cell holds entries, any number, several per kind: `outcome` (pass / fail / pending / out of scope), `kind` (lean, python, paper-claim, user-claim, llm-judged, human, ...), who and when, reasons, link to the code, `outside_fragment` flag, note. Examples: an LLM reading of what a paper says about a fact (with `presence`: in source / mentioned not tested / mentioned disregarded / not mentioned); a human saying "passes; my fragment does not implement this part but it will not matter".

**Pooling for display (changeable).** Ladder, strongest first: `lean > python > human > paper-claim > user-claim > llm-judged`. The displayed outcome is the strongest rank with an entry. If entries at that rank disagree: **conflict**, marked, never blocking. If a weaker rank disagrees with the displayed one: a small warning. The page can show every entry as chips. A pass at a stronger rank makes weaker checks unnecessary, so they are skipped unless the user asks. Informal entries are a fast first step: their reasons seed the Lean or Python version. Disagreements between kinds are flagged, never silently overwritten.

**Compute design is part of the job.** The agent is expected to think about loop structure, caching, batching and sharding (sharding is planned) before running anything large, and to say what a sweep will cost.

**Python runner: model-major.** Instantiate a model once, check every fact still pending against it (in small batches), and update the pending set; do not instantiate all models for each fact. A model that refutes a claim (a countermodel for a non-entailment, an infelicity witness) decides it at once; universal claims stay pending until the models are exhausted or a bound is reached, and the status says which (`computed on models up to size n`). Subformula evaluations are cached per model, runs are resumable per cell (sharding by model range is planned).

## Compression and plots

A good theory passes many facts with few principles. The metric choice matters (in Anaphora, Agda and Lean code sizes barely agreed in rank), which is why the page exposes it. The page offers:
- **Coverage x Complexity** with a Pareto frontier, with a dropdown for each axis. Coverage: facts passed, passed over applicable, confidence-weighted, certain ranks only, with or without `llm-judged`, with or without properties. Simplicity: number of principles, with or without auxiliary, Lean code length, Python code length.
- **Two side-by-side plots**, Complexity x Complexity and Coverage x Coverage, each axis with its own metric, to see whether the choice of metric matters.
- **A length table** comparing the same theory across implementations (Lean vs Python, or two proof assistants).
Metrics are small named functions in the registry; new ones are added by prompting.

## Starting from a topic only

The user can start with just a topic ("presupposition", "exhaustification"). The agent first looks in linglib for what already exists on the topic and reports which theories are implemented; the user picks a few (or all). Facts are then built from the papers where linglib does not already provide them, and the shared vocabulary is set up from the chosen theories. With many theories the tables get large: the page must then summarize and filter (by framework family, by status, by chosen subsets) rather than show everything. A good problem to have.

## Four activities, in any order (labels, not steps)

- **Set up:** interview (what is installed, what the user accepts to install, what is lost otherwise), the first page.
- **Integrate:** extract facts and principles from papers with source, reliability, disagreements; a paper's worked examples become facts.
- **Create (propose and repair):** propose principles, creatively or within constraints; compress facts into principles; repair a theory; propose facts that separate the top theories.
- **Exploit:** read the page, ask questions, review, plan next steps (including what data to gather next), make other views or formats.

## Two interfaces in parallel

The chat is the input; the HTML page is the output, and through the chat the user changes the page. The page has an **Ask / ideas** tab: instructions and example prompts (copy buttons), including asking for a different report altogether.

## Lean help and review

- **One Lean workspace:** a shared package for the vocabulary and one library per theory in a single Lake project (and one Mathlib, if used), never copies of the project per agent.
- **Lean guide:** before writing a principle, a fact or a proof in Lean, an LLM guide gives advice on how to set it up (general reasoning, and what worked before, for example a counterexample already found by the Python run); a subagent then writes and checks it.
- **Reviewing a paper** (each check optional, relative to our formalization): translation sheet (clause, Lean, plain English); worked examples reproduced; independent critic back-translating the Lean; typos and internal consistency (keep a Literal and a Corrected version); the paper's theorems proved or refuted; derivations re-done step by step; all facts run, including failures it does not notice; ablation of each principle for idle ones; comparison of its principles with the same ones in other papers.
- Optional: an LLM checks that outcomes are plausible; an independent reviewer audits informal judgments.
