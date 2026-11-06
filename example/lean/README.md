# Lean workspace (library `Linglab`, Lean 4.34.1, no dependencies)

`cd lean && lake build` checks everything. Shared syntax: `Linglab/Syntax.lean`; the `Theory` interface and claim shapes `Holds`/`Fails`: `Linglab/Theory.lean`.
- **Add a principle:** a def in `Linglab/Toy/Principles.lean` (or your own file) between `-- BEGIN principle:P-X` and `-- END principle:P-X`; sizes are measured on these chunks.
- **Add a theory:** copy `Linglab/Toy/T_MK.lean`, change the `Bundle` (its connectives, felicity, entailment, constraint), import it in `Linglab.lean`. `translate` returns `none` when a connective is missing: the fact is then out of scope (write no theorem).
- **Add a fact:** in each theory namespace `T_X`, write `theorem F12 : Holds theory (.felicitous [...]) := by decide` if the claim holds, or `theorem F12_fail : Fails theory (...) := by decide` if its negation holds; also add it to `Linglab/Toy/Raw.lean` (list + membership theorem).
- **Detection:** `linglab lean` runs `lake build`, then looks for `T_<theory>.<fact>` (claim proved) and `T_<theory>.<fact>_fail` (negation proved) and combines with the fact's `expected`. No theorem = no entry (pending or out of scope).
- Theory ids use underscores in Lean (`T-MK-some` is `T_MK_some`). Never leave `sorry`: a failing build means no Lean entries.
