---
name: linglab-make-a-view
description: "Build a custom view of a linglab project's data: a changed report page, a table, plot or tab, or another format (slides, a LaTeX note, a handout, a CSV) under custom/. Use when the user wants to see the data differently from the default report."
---

# make-a-view

**Use when** the user wants a different table, plot, tab, or a document: slides, a LaTeX note, a handout, a CSV.

**Read** `data/*.json`; `custom/registry.json` (metrics, ladder); `utils/template/report/template.html` for how the page is built.

**Produce**
- A page change: copy `utils/template/report/template.html` to `report/template.html` (once), edit the copy, run `report`. Register new metrics in `custom/registry.json` (the page code must implement them, so edit your copy of the template too).
- Another format: write it under `custom/` (for example `custom/slides/`, `custom/note.tex`, `custom/tables/`), generated from the data by a small script kept next to it so it can be rerun.
- Say how to regenerate it.

**Pitfalls**
- Never write into `data/` from a view, and never edit `utils/`.
- Read data; do not retype numbers. A view that hard-codes names breaks when data change.
- Keep honesty: show the kind of each result; do not show informal as formal.
- Keep it foldable, folded by default, with readable names.
- Check the result opens (a headless render or just open it) before saying it is done.
- Publishing a view is a separate step: ask first.

**Prompt**
> Make me a `<view or format>` from the current data: `<what it should show>`. Put it in `custom/`, tell me how to regenerate it, and do not change `data/`.
