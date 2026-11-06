# python/linglab

Standard-library Python (3.9+) behind `bin/linglab.py`.

- `vocab.py`: `Theory` built from `Principle`s (connectives, model constraints, vocabulary overrides).
- `runner.py`: model-major checker (one pass over the models, all undecided claims per model).
- `runcmd.py`: `linglab run` (loads the project's `python/principles.py`, writes entries).
- `check.py`, `listing.py`, `metrics.py`, `report.py`, `leancmd.py`, `init.py`, `zipper.py`: one per subcommand.
- `pooling.py`: the ladder rule of SPEC section 3.
- `proofcheck.py`: writes each fact's claim in Lean and decides which theorems `linglab lean` credits (only those that prove that claim).
- Tests: `python3 -m unittest discover -s python/tests` from the toolkit root.
- Project principles live in the project's `python/principles.py` as chunks tagged `# BEGIN principle:ID` / `# END principle:ID`.
