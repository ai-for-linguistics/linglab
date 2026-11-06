# Changelog

## 0.1.0-beta.2 — 6 November 2026

- Check compiled Lean theorems against the current fact specification before recording proof evidence; Raw Facts remain a listing baseline.
- Declare model scope, label bounded computations, and flag disagreements between implementations.
- Lean is the supported proof assistant. Existing Agda evidence can still be displayed through a custom registry, but the Agda command and workspaces are removed.
- Add optional Claude Code skills (`init --claude-skills` or `skills`); plain playbooks and other assistants remain supported.

- Record the assistant and model used for a project; treat papers as data rather than instructions.
- Mark facts delegated to another mechanism as out of scope.
- Keep plot controls inside narrow windows.
- Add report views for translations, evidence, coverage, and complexity.
- Add optional readings that explain a cell without counting as evidence.

### Updating an existing project

- Keep your data and custom files. Replace `utils/` with the new kit, then run `check`, `run`, and `lean` if you use Lean, followed by `metrics` and `report`.
- Each Lean theory namespace must expose `theory`. Only statements matching the current fact specification are credited. Declare `scope` when a model list is bounded; a declaration of completeness still needs justification.
- If you keep a custom `report/template.html`, merge the new bound and cross-check display logic into that copy.
- The `agda` command is removed. Existing Agda result entries remain readable when the project's registry includes that kind; keep or archive them as appropriate.
- Claude Code skills are optional. Run `skills` to install or refresh them; no skill installation is required for other assistants.

## 0.1.0-beta.1 — 10 October 2026

Initial beta: facts, principles, theories, Python checks, optional Lean and Agda verification, and a local report dashboard.

Future data-format changes will include migration instructions here.
