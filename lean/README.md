# Lean workspace (library `Linglab`, Lean 4.34.1, no dependencies)

The interface only; your theories go in `Linglab/Theories/`. `cd lean && lake build` checks everything.
- **Interface:** shared syntax `Linglab/Syntax.lean`; the `Theory` structure and the claim shapes `Holds`/`Fails`: `Linglab/Theory.lean`. The language-neutral specification (for any proof system) is `docs/INTERFACE.md`.
- **Worked example:** `example/lean/Linglab/Toy/` (principles as tagged chunks, four theories, facts, Raw Facts). Copy its pattern.
- **Naming:** in namespace `T_X` (the theory id with `-` replaced by `_`), `theorem F12` proves a claim, `theorem F12_fail` proves its negation; `linglab lean` combines them with the fact's `expected`. Principle code goes between `-- BEGIN principle:P-X` and `-- END principle:P-X` (sizes are measured on these chunks). A theory that cannot say a sentence returns `none` from `translate`: write no theorem, the fact is out of scope. Never leave `sorry`.
