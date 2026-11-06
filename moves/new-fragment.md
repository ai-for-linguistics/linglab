# Move: build a new fragment

**When.** A topic or paper needs its own atoms, models and semantics (the toy example is a template: `utils/example/python/principles.py`).

**Read.** `utils/python/linglab/vocab.py` (short). The example's `principles.py`.

**Also write the fragment down** in `data/fragments.json` (summary in words, definitions with words and LaTeX, code files) and reference it from each theory that uses it (`fragments`; several theories may share one, and a theory may use several).

**Produce.** `python/principles.py` in the project: one `@base_models` function, one `@principle` per principle, each in a tagged chunk (`# BEGIN principle:P-X` ... `# END principle:P-X`). Then facts and theories in `data/` (`statements.json`, `theories.json`).

**The pieces.**
- *Models.* `@base_models` returns the candidate valuations (dicts atom -> value). Values can be anything hashable; the default test of truth is `value == 1`.
- *Connectives.* `b.connective("and", fn)`: `fn(*values)` sees only the values of its arguments at one model. Enough for truth tables.
- *Operators that need more* (modals, exhaustification, anything with alternatives): `b.operator("exh", fn, arity=1)` with `fn(T, m, *subformulas)`. The operator gets the subformulas, not their values, and can evaluate them at other models: `T.value(w, sub)` for `w in T.worlds()`. The list `T.worlds()` is shared, so cached values are reused.
- *Other notions of truth or definedness.* A principle can override `true_in`, `defined_in`, `ent_ok`, `felic_ok`, `cons_ok` (`b.set(name, fn)`; `fn(T, m, ...)`), and `felic_kind`. Their meaning is theory-specific on purpose: they are vocabulary principles.
- *Sharing data between principles* (for example a set of alternatives): `b.data` is a dictionary on the builder, available afterwards as `T.data`.
- *Readable countermodels.* `b.set("describe_model", lambda T, m: "...")` controls how a model is printed in the reasons of a cell.
- *Model constraints.* `b.constrain(fn)`: models failing it are dropped for that theory.

**Quantifiers and modals.** The shared syntax has predicates, terms, binders and modals (INTERFACE.md section 1). Recipe:
1. *Models with structure.* `@base_models` yields dicts that may hold a domain and relations under keys you choose, say `vals['domain']` (a tuple of individuals) and `vals['Student']`, `vals['Passed']` (frozensets). Non-scalar entries are not atoms. Worlds are just models: `T.worlds()` is the shared list.
2. *Predicates.* `b.predicate("Passed", lambda T, m, d: int(d in m.vals["Passed"]), arity=1)`.
3. *Binders.* `b.operator("some", fn)` (also `every`, `no`, `exists`, `forall`, or your own such as `most`). `fn(T, m, x, R, S)` gets the variable name and the subformulas; evaluate the body under an assignment with `T.value(m, S, T.bind(x, d))`. Values are memoized per model and per value of the free variables.
4. *Modals.* `b.operator("may", fn)` with `fn(T, m, a)`: range over worlds with `T.value(w, a) for w in T.worlds()` (restrict them with an accessibility of your own). Inside an operator, `T.value` keeps the current variable assignment.
Worked example, "some students passed", and free choice (put each principle in a tagged chunk):
```python
holds = lambda T, m, f, x, d: T.value(m, f, T.bind(x, d)) == 1
@principle("P-SOME")
def p_some(b):
    b.operator("some", lambda T, m, x, R, S: int(any(
        holds(T, m, R, x, d) and holds(T, m, S, x, d) for d in m.vals["domain"])))
@principle("P-MAY-FC")      # free choice: may (A or B) = may A and may B
def p_may_fc(b):
    def may(T, m, a):
        if a[0] == "or":
            return int(may(T, m, a[1]) and may(T, m, a[2]))
        return int(any(T.value(w, a) == 1 for w in T.worlds()))
    b.operator("may", may)
# fact: {"type":"entailment","spec":{"premises":[["may",["or","p","q"]]],"conclusion":["may","p"]}}
# "some students passed": ["some","?x",["Student","?x"],["Passed","?x"]]
```
Without `P-MAY-FC`, a classical `may` (some world) with the entailment above fails or holds depending on the accessibility you give it: compare the two theories. A theory that defines no predicate `Passed`, or no `some`, simply leaves those facts out of scope. `linglab check` validates the sentences (arities, bound variables) and warns when no principle defines a head a fact uses. Lean and Agda carry the same syntax (`some`, `pred`, `must`, ...); their `translate` returns `none` for what they do not know.

**Pitfalls.** Helper code outside a tagged chunk is not counted in the size metrics: put shared helpers inside one chunk (or give them their own principle) so complexity is not understated. A theory that lacks an operator cannot translate sentences using it: those cells are `out of scope`, not failures, which is usually what you want. Check cheap things first: run `linglab check`, then `linglab run` on one fact.

**Prompt to paste.** "Build a Python fragment for <topic> in this project: models, the principles of <paper> as chunks, and three facts from it. Run it and show me the page."
