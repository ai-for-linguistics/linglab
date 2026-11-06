# Agda workspace (optional extra; Lean is the default)

The interface only; your theories go in `Linglab/Theories/`. Library `linglab` (Agda 2.8, `--safe --without-K`, no standard library; `Linglab/Prelude.agda` has the few helpers). `cd agda && agda Linglab/All.agda` checks everything; or `linglab agda`.
- **Interface:** `Linglab/Syntax.agda` (shared syntax S), `Linglab/Theory.agda` (record `Theory`, claim shapes, `Holds`/`Fails`). Same shape as the Lean one; the language-neutral specification is `docs/INTERFACE.md`.
- **Worked example:** `example/agda/Linglab/Toy/`.
- **Naming:** in module `Linglab.Theories.T_X` (last part of the module name = theory id with `-` replaced by `_`), `F12 : Holds theory (...)` with `F12 = refl` if the claim holds, `F12_fail : Fails theory (...)` with `F12_fail = refl` if its negation holds. Principle code between `-- BEGIN principle:P-X` and `-- END principle:P-X`. No postulates, no holes.
- **Detection:** `linglab agda` runs `agda Linglab/All.agda`, reads the `F..` / `F.._fail` signatures and combines them with the fact's `expected`. Kind `agda` ranks just below `lean`.
