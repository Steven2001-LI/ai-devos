# Implementation — TASK-0003: Task and Schema Validation

## Files Changed

- `src/aidevos/task_validation.py` (new)
- `src/aidevos/cli.py`
- `README.md`
- `tests/test_task_validation.py` (new)
- `tests/test_cli.py`
- `tests/fixtures/tasks/valid.md` (new)
- `tests/fixtures/tasks/checked_ac.md` (new)
- `tests/fixtures/tasks/extra_content.md` (new)
- `tests/fixtures/tasks/malformed.md` (new)
- `.ai/tasks/TASK-0003/status.yml`
- `.ai/tasks/TASK-0003/implementation.md` (new)
- `.ai/tasks/TASK-0003/evidence.md` (new)

The pre-approved `task.md`, `plan.md`, and `approval.md` remain unchanged.

## Implementation Summary

- Added a handwritten, standard-library-only Markdown parser and validator in the single approved
  production module `src/aidevos/task_validation.py`.
- Implemented R1 through R6 with fixed rule ordering and canonical ordering inside R2, R3, and R5.
- Added the CWD-relative `.ai/tasks/<TASK-ID>/task.md` read boundary, deterministic reporting, and
  the approved exit codes: 0 valid, 1 validation findings, and 2 usage/access failure.
- Added argparse wiring for exactly `aidevos task validate <TASK-ID>`, while preserving top-level
  help and version behavior.
- Documented repository-root usage, path resolution, and exit codes in `README.md`.
- Added no dependency and made no version change.

## Test Strategy

TDD was used. Tests were added before the production module; the initial run failed during
collection with `ModuleNotFoundError: No module named 'aidevos.task_validation'`. The minimum
implementation was then added and iterated to green.

The final 43-test suite covers the two historical live task documents, synthetic valid documents,
checked AC forms, unknown sections/Metadata, every approved negative rule case, deterministic
finding order/output, malformed and empty input, exact argument cardinality, invalid IDs without a
read, missing/directory/unreadable paths, exit-code and stream behavior, top-level CLI regressions,
and console-script/module parity. Permission and generic OSError behavior are monkeypatched and do
not rely on `chmod`.

## Commands Executed and Results

- Initial `pytest -q`: expected TDD failure; collection stopped because the new production module
  did not yet exist.
- Intermediate `pytest -q`: 40 passed after the first implementation.
- Initial `ruff format --check .`: identified three files requiring mechanical formatting; the
  files were formatted with Ruff.
- Final `pytest -q`: 43 passed in 0.61s.
- Final `ruff check .`: all checks passed.
- Final `ruff format --check .`: 6 files already formatted.
- Final `mypy src`: success, no issues in 4 source files.
- `aidevos task validate TASK-0001`: exit 0, `TASK-0001: valid`.
- `aidevos task validate TASK-0002`: exit 0, `TASK-0002: valid`.
- `aidevos --version`: exit 0, `0.1.0`.
- `aidevos --help`: exit 0 and lists the `task` command.
- `python -m aidevos task validate TASK-0001`: exit 0, matching console-script output.
- `git diff --check`: exit 0.
- `git status --short`, `git diff --stat`, and `git diff`: inspected successfully.

## Known Limitations

- Resolution is deliberately relative to the current working directory and is intended for use at
  the repository root; there is no Git-root discovery or upward search.
- Only one `TASK-ID` is supported; there is no `--path`, `--all`, or batch mode.
- Validation is structural and consistency-focused. It does not assess glob correctness, command
  quality, AC semantics, AC numbering/order/uniqueness, or other governance documents.
- The validator implements the current V4.2.1 Markdown contract directly and has no schema
  version-negotiation layer.

## Remaining Risks

The parser intentionally recognizes only the approved Markdown forms, so a future Task Schema
change will require a separate approved task. Golden validation of TASK-0001 and TASK-0002 plus the
positive-tolerance fixtures mitigate accidental over-strictness against the current contract.

## Git Confirmation

No commit was created. No branch was pushed.
