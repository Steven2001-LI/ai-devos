# TASK-0001: Repository and CLI Bootstrap

## Metadata

- Type: feature
- Priority: high
- Requested By: Human Owner
- Created: 2026-07-13

## Background

The AI-DevOS V4.2.1 protocol (`docs/AI-DevOS-V4.2.1.md`) is complete. §35 directs that the next
step is to leave the specification and create the first implementation task. TASK-0001 establishes
only the engineering foundation — a minimal, professional, installable, testable Python CLI skeleton
— with none of the AI-DevOS Gates (state machine, scope check, evidence, candidate tree, commit gate,
`init`, `task`).

## Goal

Establish a minimal, installable, testable `aidevos` CLI skeleton (`--help` / `--version` only) with
dev tooling — and none of the AI-DevOS protocol Gates.

## Scope

- `src/aidevos/`: `__init__.py` (`__version__`), `cli.py` (argparse `main`), `__main__.py`.
- `pyproject.toml`: hatchling build, PEP 621 metadata, `aidevos` console-script entry point, dynamic
  version, `[project.optional-dependencies] dev`, and `[tool.ruff]` / `[tool.mypy]` /
  `[tool.pytest.ini_options]` config.
- `tests/test_cli.py` covering `--version` and `--help` (no `tests/__init__.py`).
- `.gitignore`, `README.md`, thin `AGENTS.md` and `CLAUDE.md` pointing to `docs/AI-DevOS-V4.2.1.md`.
- TASK-0001's own repository-native governance records (hand-authored, no CLI yet):
  `.ai/tasks/TASK-0001/{task.md, plan.md, status.yml, approval.md}`.
- Documented install / test / lint / type-check commands, passing.

## Non-Goals

State machine, JSON Schema, `aidevos init`, `aidevos task`, baseline, scope check, verification runner,
candidate tree, alternate index, evidence, review gate, commit gate, worktree automation, GitHub
Actions/CI, dashboard, plugin, auto push/merge, and any runtime dependency. The generic `.ai/` scaffold
(`.ai/schemas/**`, `.ai/workflows/**`, `.ai/reviews/**`, `.ai/reports/**`, `.ai/metrics/**`,
`.ai/events.jsonl`, `.ai/constraints.yml`, `.ai/project.md`, `.ai/inbox/**`) belongs to the future
`aidevos init` task. Only `.ai/tasks/TASK-0001/**` is created.

## Acceptance Criteria

- [ ] AC-1: `pip install -e ".[dev]"` exits 0.
- [ ] AC-2: `python -c "import aidevos; print(aidevos.__version__)"` exits 0 and prints a version.
- [ ] AC-3: `aidevos` / `python -m aidevos` is on PATH after install.
- [ ] AC-4: `aidevos --help` exits 0 and prints usage.
- [ ] AC-5: `aidevos --version` exits 0 and prints the same version as AC-2.
- [ ] AC-6: `pytest -q` passes.
- [ ] AC-7: `ruff check .`, `ruff format --check .`, and `mypy src` all pass.
- [ ] AC-8: Commit not required and the working tree need not be clean. After install, tests, lint and
  type check, `git status --porcelain --untracked-files=all` shows only files TASK-0001 is allowed to
  add or modify — no `dist/`, `*.egg-info`, caches, temp files, or other unexpected products.

## Allowed Patterns

- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.gitignore`
- `src/aidevos/**`
- `tests/**`
- `.ai/tasks/TASK-0001/**`

## Restricted Patterns

- `docs/**` — protocol doc must not be modified.
- `.git/**`
- All of `.ai/**` except `.ai/tasks/TASK-0001/**`.
- `.github/**` — CI is a Non-Goal.
- `[project.dependencies]` in `pyproject.toml` must stay empty (no runtime dependencies).

## Verification Commands

- `pip install -e ".[dev]"`
- `python -c "import aidevos; print(aidevos.__version__)"`
- `aidevos --version`
- `aidevos --help`
- `python -m aidevos --version`
- `pytest -q`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `git status --porcelain --untracked-files=all`

## Dependencies

- None. Baseline commit: `7f23992`.

## Risks

- No AI-DevOS gate yet (chicken-and-egg): bootstrap cannot be enforced by the CLI it creates.
  Mitigation: Scope Proposal + Architect review is the manual gate; keep the diff tiny, enforce Allowed
  globs by eye, reviewer checks `git status --untracked-files=all`.
- Hand-authored `status.yml`: normally CLI-only atomic updates (§7.9), but no CLI exists yet — for
  TASK-0001 it is a static record, not a machine-maintained state file.
- Tool deps bounded to 3 dev tools, zero runtime deps; `pathspec` deferred.
- CLI over-engineering mitigated by stdlib `argparse`.
- `src/` single package keeps future design open; submodules drop in without restructure.
- `AGENTS.md` / `CLAUDE.md` kept thin to avoid premature governance weight.

## Rollback Notes

All changes are additive new files under the Allowed globs. Rollback = delete the created files
(`src/aidevos/`, `tests/`, `pyproject.toml`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`,
`.ai/tasks/TASK-0001/`). No existing file is modified; `docs/` is untouched.
