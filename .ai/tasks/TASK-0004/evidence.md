# Evidence — TASK-0004

> Architect fix round 1 supersedes all prior TASK-0004 pre-review verification evidence where
> results, test counts, or atomic-write ordering differ.

## Architect Fix-Round Evidence

- Review decision: `CHANGES_REQUESTED`.
- B-001: replace whole-version `int()` conversion with deterministic decimal-string carry.
- B-002: change temp-file order to write → flush → `fchmod` → `fsync` → `os.replace`, with no write
  after `fchmod`.
- Re-entry transition: exit `0`, stdout
  `TASK-0004: READY_FOR_REVIEW -> IMPLEMENTING`, status version `4 -> 5`.
- Allowed fix-round code/test writes were limited to `src/aidevos/task_transition.py` and
  `tests/test_task_transition.py`; no CLI file or CLI test change was needed in this round.
- No dependency or out-of-scope change occurred.

The B-001 red test raised an uncaught `ValueError` because the 5,000-digit input exceeded Python's
4,300-digit conversion limit. After the fix, the test verifies exact carry expansion to `1` plus
5,000 zeroes, empty stderr, byte preservation, and zero temp residue.

The B-002 POSIX regression requests mode `06750`. On a filesystem that retains set-user-ID and
set-group-ID, it asserts exact post-transition mode preservation. The current macOS temporary
filesystem strips those bits during the initial `chmod`, so the test records one explicit
filesystem-capability skip. The always-executed `0640` test continues to pass, and source inspection
plus the regression test enforce the approved write/flush/chmod/fsync/replace sequence.

## Baseline and Contract

- Baseline commit: `0b7465dab1ce02e3f1ee1f0e874a408a22d2d67d` (`0b7465d`).
- Branch: `feature/task-0004`.
- Baseline result: passed.
- Task SHA-256: `35cca4bee7f6dc6ebb6a30ed3f9578fc25bd4746fd3fdd426932abe6171ec468`.
- Plan SHA-256: `27f35640840865bf51854407fdc82af757d63caaf4e01d479b94e677bd720bb4`.
- Initial status: version `3`, `IMPLEMENTING`.

## Final Changed-Path List

Implementation and test paths:

- `src/aidevos/task_transition.py`
- `src/aidevos/cli.py`
- `tests/test_task_transition.py`
- `tests/test_cli.py`

TASK-0004 governance paths present relative to the baseline:

- `.ai/tasks/TASK-0004/task.md`
- `.ai/tasks/TASK-0004/plan.md`
- `.ai/tasks/TASK-0004/approval.md`
- `.ai/tasks/TASK-0004/baseline.json`
- `.ai/tasks/TASK-0004/status.yml`
- `.ai/tasks/TASK-0004/implementation.md`
- `.ai/tasks/TASK-0004/evidence.md`

The first five governance artifacts existed at implementation start and were the only untracked
paths. Of those five, only `status.yml` is authorized for the final CLI-driven transition; the four
frozen contract/baseline artifacts remain byte-unchanged.

## Verification Commands and Results

Final pre-transition verification:

| Command | Exit code | Result |
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

The TDD red run exited `2` during collection with
`ModuleNotFoundError: No module named 'aidevos.task_transition'`, proving the new tests initially
failed at the missing implementation boundary. The original complete repository suite passed 194
tests. Architect fix round 1 adds two test cases; the superseding result is 195 passed and one
filesystem-capability skip.

## Acceptance-Criteria Mapping

- AC-1: `test_success_updates_exactly_four_fields` verifies
  `IMPLEMENTING -> READY_FOR_REVIEW`, exit `0`, exact output, version increment, actor, and fixed UTC
  timestamp.
- AC-2: the exact-byte success assertion plus the four newline-style parametrizations, always-run
  `0640` mode test, and capability-gated POSIX `06750` test verify unrelated bytes, comments,
  ordering, nested content, trailing newline, LF/CRLF, and permissions.
- AC-3: `INBOX -> CANCELLED` is an allowed case in the exhaustive matrix and succeeds independently.
- AC-4: the disallowed-transition test and matrix verify `APPROVED -> COMPLETED`, exit `1`, exact
  error, and byte identity.
- AC-5: every `COMPLETED -> <supported target>` pair is absent and exits `1`; explicit terminal
  samples supplement the matrix.
- AC-6: all ten self-transitions are absent in the matrix; `IMPLEMENTING -> IMPLEMENTING` is also
  asserted explicitly.
- AC-7: `WOBBLE` target exits `2` with exact deterministic stderr and no write.
- AC-8: `BLOCKED` target exits `2` with the approved unsupported-state error and no write.
- AC-9: `BLOCKED` current state exits `2` with the same unsupported-state error and no write.
- AC-10: `foo` and `TASK-3` exit `2`; a monkeypatch proves no status read occurs.
- AC-11: a missing status path exits `2` with the distinct missing-file error.
- AC-12: tests cover missing and duplicate occurrences of all six required fields, explicit duplicate
  `updated_by` and `updated_at`, unsupported schema, negative and non-integer version,
  non-canonical required scalars, invalid UTF-8, and an unknown current state with exact output.
- AC-13: a status document with `task_id: TASK-9999` under TASK-0004 exits `2` and is unchanged.
- AC-14: every failure test compares original/final bytes where a file exists and checks temporary
  residue; simulated `os.replace` failure also leaves the original unchanged and cleans the temp.
- AC-15: two independent identical repositories, the same target, and the same injected instant
  produce equal codes, output, and final bytes.
- AC-16: two repeated disallowed calls produce equal codes/output and unchanged bytes.
- AC-17: console-script and `python -m aidevos` successful transitions run against independent
  copies and produce identical exit code/stdout/stderr; non-time fields are identical.
- AC-18: pytest, Ruff check, Ruff format check, and mypy all exit `0` as recorded above.
- AC-19: `pyproject.toml` is unchanged and `[project.dependencies]` remains `[]`.
- AC-20: `aidevos task validate TASK-0004` exits `0` and prints `TASK-0004: valid`.
- AC-21: `test_full_supported_state_matrix` parametrizes all `10 × 10 = 100` ordered pairs. Each
  pytest invocation receives an independent `tmp_path`; all present edges exit `0`, all absent edges
  exit `1`, and every absent edge preserves initial bytes.

## No-Write-on-Failure Evidence

The matrix compares bytes for every absent supported edge. Separate classifications compare bytes
for unknown target/current, `BLOCKED` current/target, invalid documents, task mismatch, self and
terminal transitions, and atomic replacement failure. Missing paths remain absent. All applicable
failure tests assert the same-directory temp glob `.status.yml.*.tmp` is empty afterward.

## Matrix, Preservation, and Determinism Evidence

- Supported-state matrix: 100 ordered cases, excluding `BLOCKED` and unknown tokens by design.
- Line endings: LF and CRLF, each with and without a final newline, are tested.
- Mode bits: mode `0640` is retained after replacement; exact `06750` preservation is tested on
  POSIX filesystems that retain set-user-ID/set-group-ID during setup.
- Opaque preservation: comments, ordering, unrelated fields, and nested `status`/`updated_by` keys
  remain exact.
- Determinism: fixed-clock success across independent copies and repeated failure on one unchanged
  copy are tested.
- Entry-point parity: console and module invocations use independent status files.

## Git Status and Staged-Path Evidence

Immediately before governance reports were created, `git status --short --untracked-files=all`
showed only the two tracked implementation modifications, the two new implementation/test files,
and the five original TASK-0004 governance artifacts. `git diff --cached --name-only` produced no
output. After these reports and the final status transition, the only additional paths are this
`evidence.md`, `implementation.md`, and the authorized content change to TASK-0004 `status.yml`.
No path is staged.

## Known Limitations

- `BLOCKED` lifecycle behavior, gates, actors, event history, reason capture, file locking,
  Git-root discovery, and batch operations remain deferred.
- Atomic replacement protects file integrity but does not serialize concurrent writers.
- Directory `fsync` and extended attributes are outside the approved contract.
- No new runtime dependency was introduced.
