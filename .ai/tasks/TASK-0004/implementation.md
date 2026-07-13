# Implementation Notes — TASK-0004

> Architect fix round 1 supersedes the original pre-review implementation results where counts or
> write-order details differ.

## Architect Fix Round 1

The Architect returned `CHANGES_REQUESTED` with two Blocking Issues. The real task was first
transitioned from version 4 `READY_FOR_REVIEW` to version 5 `IMPLEMENTING`; the command exited `0`
and printed `TASK-0004: READY_FOR_REVIEW -> IMPLEMENTING`.

### B-001 — Unbounded Decimal Version Increment

The prior implementation validated an arbitrary-length ASCII decimal string but converted it with
`int()`, exposing Python's configurable integer-string digit limit. `_increment_decimal` now performs
right-to-left carry directly on ASCII decimal characters and returns a string; neither validation nor
rendering converts the complete version through `int()`.

The new regression test uses 5,000 `9` digits, performs an allowed transition, and verifies exit `0`,
empty stderr, an exact result of `1` followed by 5,000 zeroes, preservation of every unrelated byte,
and no temporary-file residue. Before the fix it raised the expected uncaught `ValueError` at Python's
4,300-digit limit; after the fix it passes.

### B-002 — Preserve All Permission Mode Bits

The atomic writer now writes and flushes the complete content before applying the original
`stat.S_IMODE` value, then calls `os.fsync` and `os.replace`. No bytes are written after `os.fchmod`,
so a POSIX write cannot clear restored set-user-ID or set-group-ID bits.

The existing `0640` preservation test remains. A new POSIX test requests mode `06750` and verifies
that exact mode after transition on filesystems supporting set-user-ID/set-group-ID. The current
macOS temporary filesystem strips both bits during the test's initial `chmod`, before transition, so
that test is explicitly skipped there and will execute on a supporting POSIX filesystem. Atomic
replacement-failure byte preservation and temp cleanup remain covered.

## Files Changed

- Created `src/aidevos/task_transition.py`.
- Modified `src/aidevos/cli.py`.
- Created `tests/test_task_transition.py`.
- Modified `tests/test_cli.py`.
- Created `.ai/tasks/TASK-0004/implementation.md`.
- Created `.ai/tasks/TASK-0004/evidence.md`.
- `.ai/tasks/TASK-0004/status.yml` is the only governance file scheduled for mutation, via the
  implemented CLI after this report and the evidence record are complete.

The frozen `task.md`, `plan.md`, `approval.md`, and `baseline.json` files were not modified.

## Implementation Summary

The implementation adds one isolated transition domain module and a small additive CLI dispatch.
The domain function validates the Task ID, reads and validates the task's canonical `status.yml`,
classifies current and target states, checks the declarative transition table, renders an exact
four-field update, and atomically replaces the status file. Every rejected request returns before a
write, except simulated write failures where replacement is not performed and the temporary file is
cleaned.

## CLI and State Model

`aidevos task transition <TASK-ID> <TARGET-STATE>` accepts exactly two plain positional strings.
Argparse owns command shape and arity only; state classification remains in `transition_task`.
Existing `--help`, `--version`, and `task validate` behavior is unchanged.

The module exports the approved ten-state `SUPPORTED_STATES` tuple, `KNOWN_STATES` with `BLOCKED`
added, and `ALLOWED_TRANSITIONS` mapping every supported state to a `frozenset` of successors.
`BLOCKED` is known but unsupported and is not represented as a terminal state.

## Canonical Status-Document Validation

The validator is deliberately not a general YAML parser. It requires exactly one top-level,
unquoted, canonical `key: value` scalar for `schema_version`, `task_id`, `version`, `status`,
`updated_by`, and `updated_at`. It rejects missing or duplicate required keys, non-canonical scalar
syntax, schema versions other than `1`, a Task ID mismatch, non-integer or negative versions,
invalid UTF-8, and unknown current states. Nested similarly named fields remain opaque and are
preserved.

## Atomic Write and Preservation

All validation and edge checking complete before rendering or writing. A successful update changes
only `status`, `version`, `updated_by`, and `updated_at`. The writer uses `tempfile.mkstemp` in the
status file's directory, writes and flushes the bytes, restores the original permission mode bits
with `os.fchmod`, calls `os.fsync`, and replaces with `os.replace`. No content is written after
`os.fchmod`. The temporary path is cleaned in a `finally` block. Tests verify unrelated content,
comments, ordering, nested keys, trailing-newline behavior, LF and CRLF endings, and mode bits.

## Test Summary

TDD was followed. The first targeted run failed during collection with
`ModuleNotFoundError: No module named 'aidevos.task_transition'`. After implementation, the targeted
domain and CLI suite passed. After Architect fix round 1, the final full suite contains 195 passing
tests and one explicit filesystem-capability skip.

Coverage includes the complete 10 × 10 supported-state matrix (100 ordered pairs), all allowed and
absent edges, self and terminal transitions, unknown and `BLOCKED` state classification, Task ID and
file access failures, every required key missing and duplicated, canonical scalar validation,
schema/version/task mismatch checks, exact four-field rendering, LF/CRLF and trailing-newline
preservation, mode preservation, temporary-file cleanup, atomic replacement failure, success and
failure determinism, CLI arity, no traceback, and console/module entry-point parity.

## Commands Executed and Exact Results

Precondition and inspection commands passed on branch `feature/task-0004` at baseline
`0b7465dab1ce02e3f1ee1f0e874a408a22d2d67d`. The final pre-transition verification results were:

| Command | Exit | Exact result |
|---|---:|---|
| `pytest -q` | 0 | `195 passed, 1 skipped in 1.35s` |
| `ruff check .` | 0 | `All checks passed!` |
| `ruff format --check .` | 0 | `8 files already formatted` |
| `mypy src` | 0 | `Success: no issues found in 5 source files` |
| `aidevos task validate TASK-0004` | 0 | `TASK-0004: valid` |
| `aidevos task validate TASK-0001` | 0 | `TASK-0001: valid` |
| `aidevos --version` | 0 | `0.1.0` |
| `python -m aidevos task validate TASK-0004` | 0 | `TASK-0004: valid` |
| `git diff --check` | 0 | no output |

## Deviations from Plan

None.

## Known Limitations

- `BLOCKED`, `resume_state`, and blocker metadata are intentionally unsupported.
- The command validates graph legality only; it does not execute gates or validate actors.
- There is no event log, reason capture, file lock, Git-root discovery, batch mode, or rollback.
- The canonical line parser supports only the approved flat required scalars and preserves all
  other content opaquely.

## Remaining Risks

- Concurrent writers are outside TASK-0004; the atomic replacement prevents partial files but does
  not provide optimistic locking.
- Directory `fsync` and extended-attribute preservation were explicitly not required by the
  approved plan.

## Dependency and Git Confirmation

No runtime dependency was added; `[project.dependencies]` remains empty and `pyproject.toml` was not
modified. Nothing was staged, committed, pushed, or submitted as a pull request.
