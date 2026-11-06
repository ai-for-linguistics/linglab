# prove

**Use when** a claim should reach the top of the ladder: a fact in a theory, a no-go result, a finding. Works for Lean, and (with the same steps) for Agda or another verifier (`docs/INTERFACE.md`).

**Linglib topics:** if linglib already formalizes the theory, use linglib mode (`linglab lean --init --linglib`) and prove facts over its definitions through an adapter (`extras/linglib/README.md`); a proof then rests on linglib's definitions, which you should say.

**Read** the statement in words and as data (`data/statements.json`), the theory's principles, the interface files in `lean/` (or `agda/`), and the worked example in `utils/example/`.

**Produce** theorems named `F..` or `F.._fail` in the theory's file, then `python3 utils/bin/linglab.py lean` (or `agda`) to record them. For a general result, also a finding in `data/findings.json` with its evidence.

**The tricks**
1. **State first, prove later.** Write the statement with a hole (`sorry`) and read it against the prose: fragment, quantifiers, direction of implications. Most failures are wrong statements, not hard proofs. Use the translation sheet (`review-a-paper.md`).
2. **Find the verdict before the proof.** Search for a countermodel first: `linglab run` (model-major), or `decide` / `#eval` on the finite models. A countermodel proves the negation (`F.._fail`) and saves the proof attempt. In an earlier project, quick sketches agreed with the verifier in almost every cell: the cost was proof labour, not finding out which way it goes.
3. **Run tracks in parallel, each in its own copy of the project:** (A) formalize and prove; (B) look for a counterexample (finite models, Python, `decide`); (C) a pen-and-paper proof or at least the lemma structure. When C returns, give its lemma list to A.
4. **Draft the proof on paper before Lean:** the list of lemmas and which fact each serves. Lemmas shared by several facts are worth proving once as a kit; a good lemma costs a few rounds and halves later work.
5. **Try computation first for finite fragments:** `decide` / `refl` close a good share of the cases for free. Only then write tactics.
6. **Recycle.** A theory that is a fix of another (same principles but one) usually reuses the parent's proof terms where the changed principle is not used. Look for definitional equality before reproving.
7. **Use fast feedback, not whole rebuilds:** interactive goals or a single-file check (`lake env lean File.lean`; in Agda reload one file) take seconds, a full rebuild of everything after touching the shared interface can take many minutes. Do not edit the shared interface (`Syntax`, `Theory`) while proving; batch interface changes into one edit.
8. **Ask a guide first.** Before the first Lean or Agda proof of a project, have an LLM list the setup choices and traps for this fragment (what to import, what to make decidable, what failed before). Known traps from earlier work: classical reasoning needs an explicit excluded-middle assumption under `--safe` in Agda; universe levels spread everywhere; unsolved implicit arguments pass an interactive load but fail when another file imports the module (always confirm with the full build); `where` blocks with several pattern-matching helpers can hang the checker (move them to top level); name clashes with short names (`no`, `there`); big numeric literals in patterns.
9. **Time-box every attempt.** Each prompt to a sub-agent has a budget and a "report what you have" clause. If the proof is not converging, report the strongest lemma proved and the exact gap; the cell stays `pending`, the claim `argued` or `open`. Rough guide from an earlier project: a few fresh proofs per agent-hour; choose which cells to prove (the ones that decide a ranking or a finding), not all of them.
10. **Hygiene.** No `sorry`, no added axioms (`#print axioms` in Lean), no holes. Read the final statement against the prose once more, not just the theorem name. One folder per agent, each with its own copy of the project; at most two builds and one heavy search at a time; if an agent keeps sending the same report, stop it and take the first one.
12. **Write a reading.** When a cell is settled (or refuted), add one short entry to `data/readings.json`: how the proof or the countermodel seems to work, in plain words, `by` you, unreviewed. It is a help for the reviewer, never evidence: do not use it to change an outcome.
11. **Say what the proof is relative to:** "in our formalization", within the explored space. "No countermodel found" is `computed` with its bound, never `proved`.

**Prompt**
> Prove or refute <fact> for <theory>. First write the statement with a hole and show me how you read it. Then look for a countermodel; if there is none, draft the proof (lemma list) before writing Lean, time-box it to <N> minutes, and tell me what you got.
