# Plan — TASK-0001: Repository and CLI Bootstrap

## Current Implementation Summary

Greenfield repository. Only `docs/AI-DevOS-V4.2.1.md` exists on branch `main` (baseline commit
`7f23992`). No `src/`, `tests/`, or packaging present.

## Technical Baseline (approved)

| Decision | Choice | Reason |
|---|---|---|
| Python min version | 3.11 | Modern typing + stdlib `tomllib`; sensible 2026 floor. |
| Build system | hatchling (PEP 621) | Minimal, first-class `src/` layout, dynamic version. |
| CLI | stdlib `argparse` (no Typer/Click) | Only `--help` / `--version` needed; avoids CLI over-engineering; zero runtime deps. |
| Test framework | pytest | Used throughout the spec; §29 mandates TDD. |
| Lint / Format | Ruff (`check` + `format`) | Named in spec; single tool. |
| Type checking | mypy on `src/`, minimal config | Matches spec examples. |
| Layout | src-layout, single `aidevos` package | Standard, import-safe, extends without restructure. |
| Runtime dependencies | zero | `pathspec` etc. arrive with the features that need them. |
| Version single-source | `__version__` in `aidevos/__init__.py`; pyproject `dynamic = ["version"]`; `--version` reads it | One source of truth; testable. |

## Minimal Implementation Path

`__version__` in the package is the single source of truth. `pyproject.toml` derives the version
dynamically (hatch) and declares the `aidevos` console-script entry point → `aidevos.cli:main`.
`cli.py` builds an `argparse` parser with `--version` (`action="version"`) and default `--help`.
`__main__.py` calls `main()` for `python -m aidevos`.

## Expected Change Areas

- `pyproject.toml`
- `src/aidevos/__init__.py`, `src/aidevos/cli.py`, `src/aidevos/__main__.py`
- `tests/test_cli.py`
- `.gitignore`, `README.md`, `AGENTS.md`, `CLAUDE.md`
- `.ai/tasks/TASK-0001/**`

## Test Strategy

TDD (§29). Write failing tests first for `--version` and `--help`, invoking the CLI via `subprocess`
(installed console script) and/or by calling `main([...])` directly. Assert exit code 0 and that
`--version` prints `aidevos.__version__`. No protocol behaviour is tested — there is none in this task.

## Implementation Sequence (Engineer / Codex, minimal TDD)

1. Red: `tests/test_cli.py::test_version` — invoke CLI, assert version string. Fails (no package).
2. Add `pyproject.toml` + `src/aidevos/__init__.py` (`__version__ = "0.1.0"`).
3. Add `cli.py` (argparse `--version` / `--help`) + `__main__.py`.
4. `pip install -e ".[dev]"`; run test → green.
5. Add `test_help` (exit 0 + usage) → green.
6. Add `.gitignore`, `README.md`, thin `AGENTS.md`, `CLAUDE.md`.
7. Full gate: `ruff check .` · `ruff format --check .` · `mypy src` · `pytest -q` ·
   `git status --porcelain --untracked-files=all` shows only TASK-0001 allowed files.

## Risk Handling

See `task.md` Risks. Key control: strict Allowed globs + `.gitignore` covering build/cache artifacts so
AC-8 holds without a commit.

## Alternatives Considered

- Typer/Click for the CLI — rejected: adds a runtime dependency for a two-flag CLI; the spec flags CLI
  over-engineering as a risk. Revisit when nested subcommands (`task new/validate`) land.
- setuptools / Poetry / PDM — rejected in favour of hatchling for a lighter PEP 621 build with dynamic
  version and clean `src/` support.
