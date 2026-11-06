# Agda workspace (optional; Lean is the default)

Library `linglab` (Agda 2.8, `--safe --without-K`, no standard library; `Linglab/Prelude.agda` has the few helpers). `cd agda && agda Linglab/All.agda` checks everything; or `linglab agda`.
- **Interface:** `Linglab/Syntax.agda` (shared syntax S), `Linglab/Theory.agda` (record `Theory`, claim shapes, `Holds`/`Fails`). Same shape as the Lean one: checks are `Bool`/`Maybe` computations over a finite model list, proofs are `refl`.
- **Add a principle:** a definition in `Linglab/Toy/Principles.agda` between `-- BEGIN principle:P-X` and `-- END principle:P-X`; sizes are measured on these chunks.
- **Add a theory:** copy `Linglab/Toy/T_MK.agda`, change the bundle record, import it in `Linglab/All.agda`. `translate` returns `nothing` when a connective is missing: the fact is out of scope (write no theorem).
- **Add a fact:** in module `Linglab.Toy.T_X`, `F12 : Holds theory (felicitous (...))` + `F12 = refl` if the claim holds, or `F12_fail : Fails theory (...)` + `F12_fail = refl` if its negation holds; also list it in `Linglab/Toy/Raw.agda`.
- **Detection:** `linglab agda` runs `agda Linglab/All.agda`, then reads the type signatures `F..` / `F.._fail` of each file's module (the last part of its name, `T_MK`; `Raw` = Raw Facts) and combines with the fact's `expected`. Kind `agda` ranks just below `lean`. No postulates, no holes.
