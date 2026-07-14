# Evidence — TASK-0006

> Review 01 fix-round evidence below supersedes the original pre-review test count and AC-19 opening
> marker evidence where they differ.

## Review 01 B-001 Fix Evidence

- Review decision: `CHANGES_REQUESTED`.
- Blocking scope: B-001 only — opening context-file marker terminator `>>>>` must be `>>>`.
- Re-entry transition: `TASK-0006: READY_FOR_REVIEW -> IMPLEMENTING`, exit `0`; status version
  `11 -> 12`.
- Non-blocking Suggestions N-001 and N-002: not implemented.
- Frozen `task.md`, `plan.md`, `approval.md`, and `review-01.md`: not modified.

### Red/Green Evidence

The new `test_context_boundary_markers_use_exact_symmetric_terminators` behavior test was written
before the product fix. Its red run exited `1` and showed the generated opening line ending in
`byte_count=60>>>>` while the exact Contract-derived expected line ended in `byte_count=60>>>`.
The test also requires one exact `<<<END_AIDEVOS_CONTEXT_FILE>>>` line per opening marker.

The product change removes one `>` from the opening-marker f-string. The immediate targeted rerun
passed: `1 passed, 57 deselected in 0.02s`.

### Fix-Round Scope

Only these fix-round implementation/test paths changed:

- `src/aidevos/handoff.py`
- `tests/test_handoff.py`

TASK-local governance updates are limited to this evidence file, `implementation.md`, and
CLI-managed `status.yml`. No CLI, README, fixture, dependency, restricted file, historical Task, Git
index, branch, history, or external system was changed.

### Final Fix-Round Verification

| Command | Exit code | Actual result |
| --- | ---: | --- |
| `pytest -q` | 0 | `259 passed in 1.90s` |
| `ruff check .` | 0 | `All checks passed!` |
| `ruff format --check .` | 0 | `10 files already formatted` |
| `mypy src` | 0 | `Success: no issues found in 6 source files` |
| `aidevos task validate TASK-0006` | 0 | `TASK-0006: valid` |
| `aidevos task validate TASK-0004` | 0 | `TASK-0004: valid` |
| `aidevos --version` | 0 | `0.1.0` |
| `python -m aidevos task validate TASK-0006` | 0 | `TASK-0006: valid` |
| `git diff --check` | 0 | no output |

Final frozen hashes remain:

- Task SHA-256: `0d2ab975e507c09db36eaa6c82b03050bc83325d04ed7069cefe0432e77ef90c`.
- Plan SHA-256: `483b056dfa653df98fff86075e4907b7ce93fe3b33751b30aa041399e4267690`.
- Approval SHA-256: `4c077547bf132edc678908b99f07579e1e758ee33a2b0ffc1b6b70f96a214d19`.

`git diff --cached --name-only` produced no output. Nothing is staged, committed, or pushed.

## Gate and Contract

- Mandatory implementation gate: exit `0`.
- Branch: `main`.
- `HEAD`: `42b55ea`.
- `origin/main`: `42b55ea`.
- Gate Task validation: `TASK-0006: valid`.
- Gate status: version `9`, `APPROVED`.
- Approval Decision: `APPROVED`.
- Approved Task SHA-256:
  `0d2ab975e507c09db36eaa6c82b03050bc83325d04ed7069cefe0432e77ef90c`.
- Approved Plan SHA-256:
  `483b056dfa653df98fff86075e4907b7ce93fe3b33751b30aa041399e4267690`.
- Recomputed Task and Plan SHA-256 values matched the Approval before implementation and after final
  verification.
- Legal implementation transition: `TASK-0006: APPROVED -> IMPLEMENTING`, exit `0`.

The gate showed exactly four pre-existing untracked paths: TASK-0006 `task.md`, `plan.md`,
`approval.md`, and `status.yml`. They were preserved; only `status.yml` was mutated, through the CLI.

## TDD Evidence

The initial shell lacked `pytest` on `PATH`; the repository's existing `.venv` contained pytest and
all subsequent commands used that approved environment. The first usable targeted test run exited
`2` during collection with:

- `ModuleNotFoundError: No module named 'aidevos.handoff'`.
- `ImportError: cannot import name 'extract_non_empty_bullets'`.

This established the red phase at the missing product boundary. The final focused handoff suite
passed `57` tests, and the complete repository suite passed `258` tests.

## Final Changed-Path Scope

Implementation, documentation, and test paths:

- `README.md`
- `src/aidevos/handoff.py`
- `src/aidevos/cli.py`
- `src/aidevos/task_validation.py`
- `tests/test_handoff.py`
- `tests/test_cli.py`
- `tests/test_task_validation.py`
- `tests/fixtures/handoffs/approval.md`
- `tests/fixtures/handoffs/plan.md`
- `tests/fixtures/handoffs/task.md`
- `tests/fixtures/handoffs/context/overview.md`

TASK-0006 governance paths:

- `.ai/tasks/TASK-0006/task.md`
- `.ai/tasks/TASK-0006/plan.md`
- `.ai/tasks/TASK-0006/approval.md`
- `.ai/tasks/TASK-0006/status.yml`
- `.ai/tasks/TASK-0006/implementation.md`
- `.ai/tasks/TASK-0006/evidence.md`

Every path matches an approved Allowed Pattern. Restricted paths, historical Tasks, `pyproject.toml`,
`task_transition.py`, package version files, schemas, workflows, constraints, Git internals, and CI
were not modified.

## Verification Commands and Actual Results

Final pre-transition verification:

| Command | Exit code | Actual result |
| --- | ---: | --- |
| `pytest -q` | 0 | `258 passed in 1.90s` |
| `ruff check .` | 0 | `All checks passed!` |
| `ruff format --check .` | 0 | `10 files already formatted` |
| `mypy src` | 0 | `Success: no issues found in 6 source files` |
| `aidevos task validate TASK-0006` | 0 | `TASK-0006: valid` |
| `aidevos task validate TASK-0004` | 0 | `TASK-0004: valid` |
| `aidevos --version` | 0 | `0.1.0` |
| `python -m aidevos task validate TASK-0006` | 0 | `TASK-0006: valid` |
| `git diff --check` | 0 | no output |

`git diff --cached --name-only` produced no output. Nothing is staged.

## Acceptance-Criteria Evidence

- AC-1 through AC-3: happy-path tests assert exactly two output files, all fixed Contract fields,
  normalized identities, Task-derived Goal, allowed paths, and verification commands.
- AC-4 and AC-5: independent-root and reversed-context-order tests compare both output files byte
  for byte.
- AC-6: same-length and different-length mutations assert per-entry digest, aggregate digest, and
  canonical byte-count semantics.
- AC-7: parametrized tests cover missing/empty/whitespace Goal, missing lists, malformed/mismatched
  title, and duplicate required section with exit `1` and no output.
- AC-8 through AC-14: tests cover LF/TAB/NUL paths, absolute/traversal/backslash paths, symlink
  escapes, directories, non-UTF-8 files, duplicate/colliding paths, empty reasons, missing and invalid
  primary artifacts, supported-state membership, scalar controls/emptiness, escaping, and Task/output
  containment.
- AC-15 and AC-16: tests verify all-or-nothing publication, existing empty/non-empty/dangling-symlink
  destinations, handled write/rename cleanup, and byte preservation of primary/status inputs.
- AC-17: success and every tested failure assert stdout/stderr/exit behavior without tracebacks;
  console-script and module entry points are compared over independent repository copies.
- AC-18: the implementation uses only standard-library modules, `agent_adapter` is label-only, and
  `[project.dependencies]` remains empty.
- AC-19: prompt assertions cover identity, roles, adapter, Goal, lists, failure instruction, manifest,
  marker metadata and content, table/marker escaping, authority precedence, untrusted-data framing,
  the non-security-boundary statement, and the explicit Approval-validity disclaimer.
- AC-20 and AC-21: the complete 258-test suite and every prescribed validation, lint, format, typing,
  version, and parity command passed.
- AC-22: README now describes the completed Handoff/Context capability and contains one generation
  example while retaining Adapters, Workflow Runner, and Evaluation as planned.

## No External or Git Mutation

No network or vendor SDK was used. The generator performs no Task transition itself. No Git index,
branch, history, remote, or external system was mutated, and no commit or push was performed.
