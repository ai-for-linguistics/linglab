# INTERFACE: the Theory interface, for any proof system

Lean and Agda versions ship with the package (`lean/`, `extras/agda/`; a worked example in `example/`). This page says what they implement, so that any other proof assistant (Rocq/Coq, Isabelle, Idris, ...) can implement the same thing and the rest of the toolkit (checks, report, evidence ladder) works unchanged.

## 1. Shared syntax (version 2)
Written as JSON s-expressions in the data files; every fact written in version 1 (atoms, `not`, `and`, `or`, `if`) is still valid. A discourse is a list of sentences.

| form | JSON | Lean `S` | Agda `S` |
|---|---|---|---|
| atom | `"p"` | `atom "p"` | `atom "p"` |
| connectives | `["not",A]` `["and",A,B]` `["or",A,B]` `["if",A,B]` `["iff",A,B]` | `not` `and` `or` `imp` `iff` | `¬ₛ` `∧ₛ` `∨ₛ` `⇒ₛ` `⇔ₛ` |
| predicate application | `["Student","?x"]`, `["Passed","a"]` | `pred "Student" [.var "x"]` | `pred "Student" (varₜ "x" ∷ [])` |
| generalized quantifiers (variable, restrictor, scope) | `["some","?x",R,S]` `["every",...]` `["no",...]` | `some "x" R S` `every` `no` | `someₛ "x" R S` `everyₛ` `noₛ` |
| first-order quantifiers | `["exists","?x",A]` `["forall","?x",A]` | `exist "x" A` `forall' "x" A` | `existsₛ` `forallₛ` |
| modals (flavour left to the theory) | `["must",A]` `["may",A]` | `must A` `may A` | `mustₛ` `mayₛ` |
| theory-defined operator | `["exh",A]`, `["op",A,B]` | `op1 "exh" A`, `op2 "op" A B` | `op1`, `op2` |

**Terms** are individual constants (plain strings, `"a"`) and variables (strings starting with `?`, `"?x"`). In Lean `Term.const "a"` and `Term.var "x"` (the `?` is dropped); in Agda `constₜ`, `varₜ`.

**Reading a list.** The head decides: a reserved head (`not and or if iff must may some every no exists forall`) has the fixed shape above (binders: variable, then two formulas for `some/every/no`, one for `exists/forall`; the variable must start with `?`). Any other head followed by terms is a predicate application (at least one term). Any other head is a theory-defined operator (for example `exh`); the list of binders is open: a theory may register `most` as a binder (`["most","?x",R,S]`). Every variable must be bound by an enclosing binder; a sentence with a free variable cannot be translated.

**Scope.** Shared syntax accepts any well-formed sentence. A theory that does not define a head (or a predicate, or the atom) cannot translate it: the fact is out of scope for that theory (see 2). `linglab check` validates structure, arities and variables, and warns when no principle of the project defines an operator or predicate used by a fact.

**Lean/Agda notes.** Every `translate`/evaluator must end with a wildcard case (`| _ => none`, `eval c m _ = nothing`) so that constructors it does not know give `none`. A generic `op name (args : List S)` is a nested inductive, for which `DecidableEq` cannot be derived, so Lean and Agda carry `op1` and `op2` (add `op3` the same way if needed).

## 2. What a theory provides
- **Models:** a complete finite list (model constraints already applied).
- **translate:** shared syntax -> the theory's own formula, **partial**. `none` means the theory cannot express the sentence: the fact is *out of scope* (neither pass nor fail).
- **trueIn(model, formula)** and **definedIn(model, formula)** (not undefined).
- **Vocabulary, each the theory's own notion:** `ent(premises, conclusion)` consequence; `felic(discourse)` felicity in the null context; `cons(premises)` consistency. Everything is decidable and computed over the finite model list, so proofs are by computation (`decide`, `refl`, `native_decide`, ...).

## 3. Claims and verdicts
A claim has one of four shapes over the shared syntax: `entails(premises, conclusion)`, `felicitous(discourse)`, `consistent(premises)`, `truth(sentence, rel, target)` with `rel` one of equals, within, includes (a truth set against another's). Equivalence is two `entails` (grouped as one fact).
`check(theory, claim)` is `none` (out of scope) or `some b`. `Holds` means `check = some true`, `Fails` means `check = some false`. `Fails` is **not** the negation of `Holds`: out of scope proves neither, so nothing is vacuously true.

## 4. From theorems to cells
In a unit named after the theory (a namespace or module; the theory id with `-` replaced by `_`, so `T-MK-some` is `T_MK_some`), write for each fact `F12`:
- `F12` proving `Holds theory claim`, if the claim holds;
- `F12_fail` proving `Fails theory claim`, if the claim fails.
No theorem means no entry (pending, or out of scope if `translate` gives `none`). The tool combines the theorem with the fact's `expected`:

| fact expects | claim proved (`F12`) | negation proved (`F12_fail`) |
|---|---|---|
| holds | pass | fail |
| fails | fail | pass |

Never accept `sorry`, postulates, axioms added for the purpose, or holes: a build with any of them yields no entries.

## 5. Principles as chunks
Principle code sits between two comment lines in the language's comment syntax: `BEGIN principle:P-ID` and `END principle:P-ID` (`-- ` in Lean and Agda, `# ` in Python). Sizes (complexity metrics) are measured on these chunks with comments and blank lines removed. Helper code outside a chunk is not counted: put shared helpers inside a chunk of their own.

## 6. Raw Facts
A unit `Raw` lists every fact's claim with its expected outcome and proves, for each, that it is listed (membership). It is a theory like any other (`RAW`): maximal coverage by construction, and a check that the facts do not contradict each other.

## 7. Adding another verifier
1. Implement sections 1 to 6 in the proof assistant, as naturally as it allows (finite, decidable, proofs by computation).
2. Choose a short name for the verifier (for example `coq`) and add it to the `ladder` in `custom/registry.json`, at the rank you want (default: just below `lean` and `agda`, above `python`).
3. Ask the assistant to add a `linglab <name>` command modelled on `python/linglab/leancmd.py` (build, find the `F..` and `F.._fail` theorems, write entries of kind `<name>`), or have it write the `results.json` entries by hand (`kind`, `outcome`, `ref` = the file, `reasons`, `who`). Either way, entries must come from a successful build.
4. Run `linglab check`, then `linglab report`: the new kind appears in the heatmap (a proof kind gets the dot if listed in `registry.proof_kinds`; any kind that is not python, lean or agda is drawn as informal evidence) and in the evidence ladder.

## 8. Reusing a library of formalized theories (linglib mode)
A proof-assistant library that already formalizes theories can be reused by writing adapters that build a `Theory` from the library's definitions, over a finite decidable layer (see `extras/linglib/README.md` for the Lean and linglib case: `linglab lean --init --linglib`). Size metrics then measure only the adapter, not the library.

## 9. Extending the interface
Version 2 of the syntax (section 1) already covers predicates, individual terms, quantifiers and modals; the models of a fragment may hold a domain and relations under keys the project agrees on (in Python, `vals['domain']`, `vals['P']`), and operators read them. New constructs beyond these (plurals, counting as such, events) mean new constructors in the syntax, optional new fields in the theory (with defaults), and new claim shapes next to `check`. Do it in batches: changing the interface changes the meaning of many facts, and in the Agda project editing the shared syntax forced a rebuild of almost everything.

## 10. Probes, text or spec, reasons for out of scope (proposed)

Status: **partly implemented** (the out-of-scope reasons and the parses of a fact, in the Python runner, the checker and the report); probes, `reads: text` and the primitive-proposal registry are proposals. The rationale is in `MODEL.md`, section "Facts, probes and linking hypotheses".

- **Fact fields.** `text` (always), `spec` (zero, one or several pivot formulas, each with an `id`; one per reading when the sentence is ambiguous), `probe` (judgment, inference, comparison, scenario, preference), `response` (expected label or value), `context`.
- **Theory field `reads`:** `spec` (default) or `text`. A theory that reads text declares its parser as principles (`role: parser`).
- **Linking hypothesis.** A theory's adapter maps a probe and a response to a prediction, or to none. `translate` returning none is *out of scope, reason fragment*; no linking for the probe is *reason no-prediction*; an unimplemented primitive is *reason primitive*.
- **Entries.** An out-of-scope entry carries `reason` in {fragment, no-prediction, primitive}.
- **Primitive proposals.** A file or registry entry with `name`, `definition`, `example`, `proposed_by`, `relations`. A theory lists the primitives it implements.
- **Versioning.** The syntax version and the registry of primitives are part of every exchanged statement and result, so that an entry can be recognised as stale or incompatible.


## 10. What the report page reads (display contract)
The page is generic: it needs no change when a verifier or a theory is added. What it reads:
- **Entries** (`data/results.json`): `kind` decides the marks of a heatmap square (a kind listed in `registry.proof_kinds`, default `lean` and `agda`, gets the dot; any kind outside python and the proof kinds is informal and gets the stripes; two entries of the top rank that disagree, or a weaker kind that disagrees, give the cross); `outcome` gives the colour; `presence`, `bound`, `reasons`, `note` and `ref` are shown in the panel's third part (current test). A verifier's theorem statements are shown there too, taken from the `BEGIN`/`END` or namespace conventions of sections 4 and 5, for the theory and for the theories of its **family** (a modified theory shares the formalization of its source; the panel says so).
- **Theories**: `family` groups the rows when there are two or more families; `kind` (`original`, `fix`, `creative`, `reference`) labels the rows of a family (Source, Modified, New; the labels are `meta.theory_kinds`); `short` is the display code used in running text; `parent` and `origin` fill the origin table of the Overview; `fragments` fill the panel's second part.
- **Facts**: `kind` groups the columns (default `type`), `layer` the reliability sets of the bar summaries and of the data filter (`registry.layers` orders and names them; default controversial / uncontroversial from `contested`), `requires` names the fragment the fact needs.
- **Page**: `meta.page_title`, `meta.subtitle`, `meta.paper`, and the warning band (`meta.banner`, `banner_title`, `banner_points`) are plain strings; nothing is required.
Honesty guardrails are part of the contract: every cell says how it was obtained, informal evidence is never drawn like a run or a proof, and conflicts are shown, never hidden.

**Implemented so far** (Python runner; Lean and Agda results carry no reason yet):
- `scope` on an out-of-scope entry: `fragment` (translate gives none), `primitive` (the theory declares `primitives` and the fact's type or `uses` is not in the list), `no_prediction` (the theory declares `predicts` and the fact's type is not in the list).
- Several parses: a fact has `spec` (parse `main`) and optional `parses`; the theory's `parse_policy` and `picks` decide which parses it evaluates and how it combines them; the entry records `parses` (`{id: outcome}`) when more than one was evaluated.

