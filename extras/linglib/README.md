# Linglib mode (optional): Lean cells that reuse linglib

[linglib](https://github.com/linglib-community/linglib) is a Lean 4 + Mathlib library of formalized linguistic theory (Apache-2.0; it says itself that it is AI-assisted and may contain errors). In this mode your Lean workspace depends on it, so a theory already formalized there can be wrapped as a `Linglab.Theory` instead of being re-implemented, and facts about it are proved over linglib's own definitions.

**Created by** `python3 utils/bin/linglab.py lean --init --linglib`: the usual interface (`Linglab/Syntax.lean`, `Linglab/Theory.lean`) plus a `lakefile.toml` that requires linglib at a tag, a `lean-toolchain` pinned to linglib's version, and a worked adapter (`Linglab/Theories/FoxIE.lean`).

**Before fetching anything, tell the user:** the project's Lean version changes to linglib's (v4.34.0); the first `lake update` downloads linglib and Mathlib (an estimated 2 GB download, about 7 GB on disk, 5 to 20 minutes the first time); linglib may contain errors. If a Mathlib checkout at the same revision exists on the machine, it can be copied into `lean/.lake/packages` before `lake update` to skip the download. Then: `cd lean && lake update && lake build`.

**Writing an adapter** (`Linglab/Theories/<Name>.lean`, import only the linglib modules you need, never `import Linglib`):
- The model is whatever finite type makes the theory decidable (in the example, a world is a `Fin 16` coding which valuations are accessible); a form is a `Finset` of worlds. Use linglib's decidable `Finset` layer (for example `Exhaustification.Finite`), so the Bool `Theory` works unchanged and facts are proved by `decide`.
- `translate` maps the shared syntax to forms; operators such as `exh` arrive as `op1 "exh" a`. Linglib has no syntax layer (propositions are `Set W`), so each adapter writes its own translation and its own alternatives.
- For results that exist only over `Set` (not decidable), state a fact directly over linglib's definitions as a `Prop` and cite its theorem; such entries are `lean` evidence too, but be explicit in `reasons` about what was proved.
- Facts: in `namespace T_<Name>`, `theorem F12 : Holds T (...) := by decide` (or `F12_fail`), as in `docs/INTERFACE.md`.

**Caveats.** Size metrics measure only the adapter, not the linglib definitions it uses, so a theory built on linglib looks smaller than it is. The toolchain moves in step with linglib's releases. Check that an adapter's hand-written pieces (for example the second exhaustification layer in the example) agree with linglib's own definitions, or say that they have not been proved equal.
