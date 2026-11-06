# Contributing

The toolkit is in `python/linglab/`; project templates are in `template/`; `example/` is a worked fragment. Edit the introduction in `slides/index.html`. User instructions live in `BOOTSTRAP.md`, `GUIDE.md`, and the task playbooks in `moves/`.

## Check and build

```sh
python3 -m unittest discover -s python/tests
node template/report/smoke_test.js example/report/index.html
python3 bin/linglab.py zip
python3 bin/linglab.py site
```

The site is built in `dist/site/`. Pushes to `main` publish it with GitHub Pages. Build outputs are ignored.

Keep results honest about their evidence and verification. Preserve existing project data when adding features. Document data-format changes and migrations in `CHANGELOG.md`.

## Assistant playbooks

Keep `moves/` usable as plain Markdown for any assistant. Claude Code copies are optional: `init --claude-skills` or `skills`. Do not make normal initialization, checks, or report generation depend on a vendor-specific skill loader.
