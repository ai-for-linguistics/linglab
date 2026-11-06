# GUIDE: for you, the linguist

## Arrange your screens

- One side: your assistant's chat (a terminal, the desktop app, or an editor such as VS Code). This is where you talk.
- Other side: a browser window with `report/index.html`. This is what you read.
- After each step the assistant rebuilds the page. Reload it.

## Two interfaces

The chat is your input. The page is the output. You can change the page by asking in the chat ("add a column", "show this as a table by framework", "make a slide deck from this").

## How to move forward

You are in charge. Ask anything, any time, in plain words. The assistant ends each message with what changed, where to look, and one suggested next step. You can ignore it.

Examples of prompts:
- Set up: "My question is ... Here are three papers. Tell me what you think is missing."
- Integrate: "Extract the data from `<paper>` as facts." "Extract its theory as principles."
- Create: "Theory X fails fact F03. Propose the smallest fix." "Propose a smaller theory that passes the same facts."
- Check: "Run everything pending." "Check F05 in Lean."
- Review: "Review `<paper>` in our formalization, with an independent critic."
- Exploit: "Where do we stand?" "Which facts separate the top two theories?" "What data should I gather next, and what will it cost?"
- Page: "Make a different report." "Export a LaTeX table of the matrix." "Make slides."
- Tools: "Use a different proof system for the formal checks." "Run the Python checks over more models, but tell me the cost first."

## What the labels mean

Outcome of a cell:
- `pass`: the fact's expected outcome was met.
- `fail`: it was not.
- `pending`: not tested yet.
- `out of scope`: the theory cannot express the fact, or its source says the fact is handled by a mechanism the theory leaves out (for example, a logic of free choice that leaves scalar implicatures to a separate mechanism). Not a failure.

How it was obtained (strongest first): `lean` (machine-checked), `python` (computed on all models, or on the first n, as the cell says), `human` (you or a colleague), `paper-claim` (a paper says so), `user-claim`, `llm-judged` (the assistant's reading, the weakest).

Take-home messages use: `proved`, `computed`, `argued`, `literature`, `open`.

A conflict means two results of the same strength disagree. A warning means a weaker kind disagrees with the one shown. Neither blocks anything. Nothing is silently overwritten.

**Out of scope has three reasons**, shown in the cell panel: the sentence cannot be stated in the theory (*fragment*), the theory makes no prediction for this kind of fact (*no prediction*), or the fact uses a notion the theory does not implement (*primitive*), including one its source leaves to another mechanism. None of them is a failure.

**Parses.** A sentence can be parsed in several ways. The fact keeps the sentence and the judgment; the theory chooses which parse (or parses) it uses to make its prediction, and says how it combines them. The panel lists the parses of a fact and the verdict per parse.

**Readings.** In a cell's panel, the part called *Reading* is the assistant's own explanation of what happened (for example how a proof seems to have worked). It is written to help you review; it is not evidence and does not change any verdict. You can accept it or correct it ("Correct the reading of F02 x T-SK: ...").

## When you are stuck

- Ask: "What can I do now?" or "Explain this page."
- If the assistant seems lost: "Stop. Tell me what you did last and what you plan."
- If a result looks wrong, ask for the countermodel in plain words, or for a second opinion from a fresh reviewer.
- If it spends too long: "Stop background work. Report what you have."
- If costs worry you: "What would this cost in compute and tokens?" before you say go.
- Nothing is published or shared unless you say so.

## Optional Claude Code skills

The toolkit works with any assistant that can read files and run commands. The playbooks in `utils/moves/` remain plain Markdown; a skill loader is not required.

In Claude Code, ask the assistant to run `python3 utils/bin/linglab.py skills`. New projects can use `init --claude-skills`. Run `skills` again after updating the toolkit to refresh its copies; unrelated skills are preserved.

## Stop and resume

Stop whenever you like. Everything is in the folder. Later, open the assistant in the project folder and say: "Read utils/BOOTSTRAP.md". `AGENTS.md` and `CLAUDE.md` in the folder do this automatically in most assistants.

## Where files are

- `brief.md`: your question, goals, papers.
- `data/`: facts and principles (`statements.json`), theories, results, findings, metadata.
- `report/index.html`: the page. The **Theories × Facts** tab is a heatmap: one square per fact and theory, green pass, red fail, grey out of scope, empty pending; a dot means a machine-checked proof, stripes mean informal evidence, a cross means conflicting results, a yellow cross marks a controversial fact (its row or column is paler and comes last in its kind). Click a square (or a bar) for the details in the panel at the bottom; the toggle turns the table. **Coverage × Complexity** plots coverage against complexity: pick the proxy on each axis, filter the data, hide groups of theories. The theory cards are the last block of **Theoretical Space** (`#cards:ID` links open them). The page title, subtitle, warning band, display names, kinds and families are all optional settings, described in `utils/docs/SPEC.md` (display options); the browser's back button returns to the previous tab and scroll position.
- `literature/`: your PDFs, named `Author_Year_ShortTitle.pdf`.
- `custom/`: your own changes (metrics, ladder, notes). A changed page template goes in `report/template.html`.
- `utils/`: the package. Do not edit; ask the assistant for changes and it puts them in `custom/`.

## Big requests

For a big request (many theories, many papers) the assistant first proposes a plan and asks for a budget, starts with two theories and one paper, keeps a Done / Next / Budget note in `brief.md`, and widens in batches with a check-in each time. You can always say "stop", "smaller", or "go on".

## Versions and updating

The toolkit has a version (`utils/VERSION`, with the build date in `utils/BUILD.json`); it is shown at the bottom of the report and recorded in `data/meta.json` when the project is created. The page you downloaded it from shows the version too. To update: download the new package, replace the `utils/` folder with it (your `data/`, `custom/`, `report/` and `literature/` stay), then ask the assistant to run `check` and `report`; `utils/CHANGELOG.md` says whether data formats changed and how to migrate.

## Credits and tokens

Heads up: working with an AI assistant uses credits or tokens, and long jobs (many theories, many models, proof searches) can use them up quickly. The assistant should tell you the cost of a big step before running it; you can always ask "what will this cost?" and set a budget.

## A word of caution

Beta. Produced with AI assistance. Results may be wrong: check them (especially the translation of statements into code) before drawing scientific conclusions. Amend them by hand where needed. Iterate. The page tells you how each cell was obtained; the Translations tab is where you check that the words and the code say the same thing.
