# Task Approval

- Task: TASK-0003
- Decision: APPROVED
- Scope Proposal: Rev. 2
- Reviewed Task Hash: n/a (no CLI verify gate yet — hashes begin once `aidevos verify` exists)
- Reviewed Plan Hash: n/a (no CLI verify gate yet)
- Approved By: Human Owner / Architect
- Approved At: 2026-07-13

## Scope Assessment

Scope Proposal Rev. 2 approved. TASK-0003 implements the first AI-DevOS validation gate: a
deterministic `aidevos task validate <TASK-ID>` command that validates a single
`.ai/tasks/<TASK-ID>/task.md` against the AI-DevOS V4.2.1 §8 Task Schema, using handwritten
standard-library Markdown parsing with **zero new runtime dependencies**. The command accepts
exactly one positional `TASK-ID` argument matching `^TASK-[0-9]{4}$`, resolves the target file as
`.ai/tasks/<TASK-ID>/task.md` relative to the current working directory (no Git-root discovery, no
upward search, no `--path`, no batch/`--all` mode), and is intended to be run from the repository
root.

Approved goal: add `aidevos task validate <TASK-ID>` returning a stable pass/fail result, with
parsing and validation in the single new module `src/aidevos/task_validation.py` and CLI wiring in
`src/aidevos/cli.py`.

Allowed implementation files: `src/aidevos/cli.py`, `src/aidevos/task_validation.py`,
`tests/test_cli.py`, `tests/test_task_validation.py`, `tests/fixtures/tasks/**`, `README.md`, and
`.ai/tasks/TASK-0003/**`.

Restricted / must remain untouched: `docs/AI-DevOS-V4.2.1.md`, `src/aidevos/__init__.py` (no version
bump), `src/aidevos/__main__.py`, `pyproject.toml` (dependencies stay empty), `.ai/schemas/**`,
`.ai/tasks/TASK-0001/**`, and `.ai/tasks/TASK-0002/**` (read-only golden fixtures).

Out of scope: lifecycle state transitions, `status.yml` validation, JSON Schema / `.ai/schemas/`,
scope-versus-git-diff enforcement, evidence generation, Git candidate snapshots, review/commit
gates, `aidevos init`, dashboard/daemon/cloud behavior, and any unrelated CLI refactoring.

## Architecture Assessment

Adds an argparse `task` command group and `validate` subcommand; `main()` dispatches and returns the
handler's exit code while preserving existing `--help` / `--version` behavior. Parsing and rule
evaluation are consolidated in one production module, `src/aidevos/task_validation.py` — no split
into multiple modules. No new dependency, no version bump (`src/aidevos/__init__.py` stays `0.1.0`);
`[project.dependencies]` remains empty. Validation targets the §8 Markdown contract directly, with no
JSON Schema file layer.

### Approved validation contract (R1–R6)

- **R1 — Title.** Leading blank lines allowed; the first non-empty line must match
  `# TASK-XXXX: <non-empty title>`; any content before the title fails R1.
- **R2 — Required sections.** The twelve required sections, each present once, any order, extras
  allowed; a duplicate required section fails.
- **R3 — Metadata.** `Type`, `Priority`, `Requested By`, `Created` required and non-empty; `Type`
  and `Priority` enum-checked; extras allowed; a missing, empty, or duplicated required field fails.
- **R4 — Acceptance Criteria.** At least one accepted AC item in one of the forms
  `- [ ] AC-N: <non-empty text>`, `- [x] AC-N: <non-empty text>`, or `- [X] AC-N: <non-empty text>`;
  validation fails only when the section contains no accepted item in any of those three forms.
- **R5 — Required non-empty lists.** Allowed Patterns, Restricted Patterns, Verification Commands
  each have at least one non-empty bullet.
- **R6 — Task ID consistency.** The R1 title Task ID must equal the CLI argument; if no valid title
  Task ID is parsed, no R6 finding is emitted.

Malformed or empty Markdown is a robustness requirement (deterministic R1/R2 findings, no
traceback), not a separate rule. Deterministic finding order is R1 → R2 → R3 → R4 → R5 → R6 with the
canonical section, Metadata-field, and required-list ordering within each rule.

### Exit-code contract (binding)

- 0 — valid task document.
- 1 — task document validation failure (a well-formed argument and a successfully read file, but one
  or more contract rules fail).
- 2 — invalid CLI usage, invalid `TASK-ID` argument format, missing file, or unreadable/failed file
  read (e.g. `PermissionError`/`OSError`); in the exit-2 access case stdout is empty, stderr carries
  a clear access-error message, and no traceback is emitted.

Usage/access failures (exit 2) are decided before document parsing; only a valid argument plus a
successful read can reach an exit-0/1 outcome.

## Acceptance Criteria Assessment

AC-1..AC-23 are independently testable. The two historical task files must pass unchanged
(`aidevos task validate TASK-0001` and `aidevos task validate TASK-0002` → exit 0; AC-1, AC-2).
Positive tolerance is covered by AC-4 (checked `[x]`/`[X]` forms) and AC-5 (unknown extra section
and Metadata field). Negative cases cover missing required section (AC-6), title not the first
non-empty line (AC-7), invalid enums (AC-8), an empty Metadata value (AC-9), a required Metadata
field absent entirely (AC-10), an Acceptance Criteria section with no accepted `[ ]`/`[x]`/`[X]`
AC item (AC-11), empty required lists (AC-12), duplicate required section (AC-13), duplicate
Metadata field (AC-14), Task-ID mismatch (AC-15), and empty/title-less Markdown with deterministic
findings and no traceback (AC-19).

Usage/access cases assert exit 2 for a bad `TASK-ID` format with no file read (AC-16), a missing
file (AC-17), and an unreadable/failed read (AC-18) — the last verified through a controlled
mock/monkeypatch of the file-read operation, with exit 2, a clear stderr access message, empty
stdout, and no traceback, not via `chmod` or OS permission semantics. Determinism is asserted
byte-for-byte across repeated runs (AC-20). No-regression is AC-21. The tooling gate (AC-22)
requires `pytest -q`, `ruff check .`, `ruff format --check .`, and `mypy src` all green; AC-23
requires runtime dependencies to remain empty.

**Binding rule:** a duplicate occurrence of any required Metadata field (`Type`, `Priority`,
`Requested By`, `Created`) is a validation failure. The validator must not resolve duplicates by
first-wins or last-wins; it must report the duplicate and fail (exit 1). The same rejection applies
to a duplicate occurrence of any required section.

## Conditions

- Zero new runtime dependencies; `[project.dependencies]` stays empty; validation is handwritten
  stdlib only.
- Parsing and validation live solely in `src/aidevos/task_validation.py`; CLI wiring stays in
  `src/aidevos/cli.py`.
- Path resolution is CWD-relative to `.ai/tasks/<TASK-ID>/task.md`; no Git-root discovery, no
  `--path`, no batch mode. Document that the command runs from the repository root.
- Historical task files `.ai/tasks/TASK-0001/**` and `.ai/tasks/TASK-0002/**` and
  `docs/AI-DevOS-V4.2.1.md` must not be modified.
- Commit Policy: no commit or push during planning or implementation; commit is allowed only after
  final approval and through the designated release step.

## Status Note

Approval only. Implementation has not started; no production code or tests have been written, and
nothing has been committed or pushed. No verification commands have been run and no tests are claimed
to pass.
