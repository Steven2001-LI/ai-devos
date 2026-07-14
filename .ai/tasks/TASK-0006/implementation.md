# Implementation Notes — TASK-0006

> Review 01 fix-round results below supersede the original pre-review test count and AC-19 marker
> details where they differ.

## Review 01 Fix Round — B-001

Review 01 returned `CHANGES_REQUESTED` with one Blocking Issue. TASK-0006 was legally transitioned
from status version 11 `READY_FOR_REVIEW` to version 12 `IMPLEMENTING` before any fix-round code or
test change.

B-001 identified that `_render_prompt_pack` emitted each opening context marker with four closing
angle brackets (`>>>>`) instead of the frozen Contract's exact three-bracket terminator (`>>>`). A
behavior regression test was added first. It constructs the exact expected opening line for every
manifest entry from `path`, `sha256`, and `byte_count`, compares the generated opening lines in
manifest order, and verifies one exact `<<<END_AIDEVOS_CONTEXT_FILE>>>` line per opening marker.

The red test exited `1` and showed the precise mismatch `byte_count=N>>>>` versus
`byte_count=N>>>`. The product fix changes only that one output character in
`src/aidevos/handoff.py`. The targeted regression then passed, and the final complete suite passed
259 tests.

Fix-round implementation changes are limited to:

- `src/aidevos/handoff.py` — change the opening marker terminator from `>>>>` to `>>>`.
- `tests/test_handoff.py` — add the exact opening/closing marker regression test.
- `.ai/tasks/TASK-0006/implementation.md`, `evidence.md`, and CLI-managed `status.yml` — record the
  fix round and legal transitions.

Non-blocking Suggestions N-001 and N-002 were not implemented. No CLI, extractor, README, fixture,
dependency, architecture, or unrelated behavior changed. Frozen `task.md`, `plan.md`, `approval.md`,
and `review-01.md` were not modified.

Final fix-round verification:

| Command | Exit | Actual result |
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

## Implementation Summary

TASK-0006 adds the approved deterministic `aidevos handoff generate` vertical slice. The command
validates the Task Contract before extraction, safely canonicalizes the three primary artifacts and
an explicit reason-annotated context allowlist, constructs Handoff Contract v1 plus a fixed
model-independent Prompt Pack in memory, and publishes both files together under the Task-local
handoff directory without overwriting an existing destination.

The implementation uses only the Python standard library. `agent_adapter` remains a normalized
descriptive label, `failure_return_state` is checked only for supported-state membership, and the
command performs no Agent invocation, lifecycle transition, Approval validation, Scope enforcement,
verification execution, Evidence generation, or network access.

## Design Decisions

- `task_validation.py` exposes two additive extractors that reuse `_parse_sections` and
  `NON_EMPTY_BULLET_PATTERN`; the existing R1-R6 validator and reporting behavior are unchanged.
- Every input file is strict-UTF-8 decoded, stripped of one leading BOM, normalized to LF, and then
  hashed and embedded from the same canonical bytes.
- Manifest entries and context blocks are sorted by normalized repository-relative path UTF-8 bytes.
  The aggregate digest uses only each entry's path, SHA-256, and canonical byte count.
- Path and scalar control characters are rejected before unsafe values can be rendered. Context
  paths additionally reject absolute paths, parent traversal, and backslashes, and resolved paths
  must remain inside the declared Repository Root.
- Output bytes are prepared before any output directory is created. Publication uses a temporary
  sibling directory, file and directory `fsync`, and same-filesystem atomic rename; handled failures
  remove temporary residue and a newly-created empty parent.
- Existing destinations include dangling symlinks and are never overwritten.

## Files Changed

- Created `src/aidevos/handoff.py`.
- Modified `src/aidevos/cli.py`.
- Modified `src/aidevos/task_validation.py`.
- Created `tests/test_handoff.py`.
- Modified `tests/test_cli.py`.
- Modified `tests/test_task_validation.py`.
- Created the minimal `tests/fixtures/handoffs/**` fixture set.
- Modified `README.md` with the implemented capability statement and one generation example.
- Created this implementation record and `.ai/tasks/TASK-0006/evidence.md`.
- Updated `.ai/tasks/TASK-0006/status.yml` only through legal CLI transitions.

The frozen `task.md`, `plan.md`, and `approval.md` were not modified. Their final SHA-256 values
remain exactly those bound by the Approval.

## TDD Record

Behavior tests were written before product implementation. The first usable targeted run exited `2`
during collection because `aidevos.handoff` and the new extractors did not exist. After the initial
implementation, focused tests exposed three contract/test-harness issues, which were corrected. A
later red test demonstrated that a dangling destination symlink could reach the generic publication
failure path; the implementation was tightened to classify any existing symlink as an existing
destination and preserve it.

The final suite has 258 passing tests. New coverage includes successful generation, exact Contract
fields and ordering, Task-derived Goal/lists, cross-root and context-order determinism, canonical
hash/byte-count changes, all required invalid-Task samples, path/scalar safety, duplicate and empty
reason classification, primary artifact failures, output containment, collision refusal, write and
rename cleanup, prompt framing/escaping, and console/module parity.

## Deviations from Plan

None.

## Known Limitations

- Publication intentionally provides the approved single-process model; it does not lock or claim
  cross-process TOCTOU safety.
- Boundary markers provide stable framing but are not a security boundary; embedded Repository
  context remains untrusted data.
- Approval hashes and authority are not validated, and extracted allowed paths and verification
  commands are not enforced or executed. These remain deferred to TASK-0009.
- Adapter execution and workflow/lifecycle orchestration remain deferred to TASK-0007 and TASK-0008.

## Remaining Risks

The remaining risks are the explicitly approved limitations above. Determinism, containment,
never-overwrite behavior, cleanup, CLI error classification, and regression behavior have automated
coverage and passed the complete verification sequence.

## Dependency and Git Confirmation

`pyproject.toml` is unchanged and `[project.dependencies]` remains empty. No file is staged. No
commit, push, branch, worktree, pull request, tag, merge, or release operation was performed.
