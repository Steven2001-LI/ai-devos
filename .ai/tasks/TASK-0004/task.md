# TASK-0004: Declarative Task State Transitions

## Metadata

- Type: feature
- Priority: high
- Requested By: Human Owner
- Created: 2026-07-13

## Background

TASK-0001 established the installable `aidevos` CLI skeleton, TASK-0002 aligned product positioning,
and TASK-0003 added deterministic `aidevos task validate` for the §8 `task.md` contract. AI-DevOS
V4.2.1 §7.9 makes `status.yml` the single source of truth for a task's dynamic lifecycle state and
§11.2 requires that it be mutated only by atomic CLI updates that validate the From→To transition;
§10–§11 define the state graph. TASK-0002 records declarative state transitions as roadmap #3, and
TASK-0003 explicitly deferred "Lifecycle state transitions and the state machine" to this task.

Today every `status.yml` is hand-edited: nothing prevents an illegal jump (for example
`PLANNING → COMPLETED`, or a mutation out of a terminal state), nothing bumps `version`, and nothing
guarantees an atomic, field-preserving write. Because every later gate keys off `status`, an
unguarded state field undermines the whole governance chain. TASK-0004 adds one declarative,
machine-checked transition command with a safe atomic writer — graph legality only, no gate
execution.

## Goal

Add a deterministic `aidevos task transition <TASK-ID> <TARGET-STATE>` command that, driven by a
declarative supported-transition table, performs a state change if and only if it is a supported
transition from the task's current `status`, atomically updating exactly `status`, `version`,
`updated_by`, and `updated_at` in a canonical AI-DevOS `status.yml` (preserving all other content)
and making no change on any failure — with stable, scriptable exit codes (0 performed, 1 disallowed
edge, 2 usage / unsupported-state / invalid-document). Implementation lands in one new module
`src/aidevos/task_transition.py` with CLI wiring in `src/aidevos/cli.py`; no new runtime dependency.

## Scope

- `src/aidevos/task_transition.py` (new): `SUPPORTED_STATES`, `KNOWN_STATES`, `ALLOWED_TRANSITIONS`
  data table; a canonical-`status.yml` validator; `transition_task(task_id, target_state, cwd=None,
  now=None) -> int` performing ID guard → read → document validation → state classification → edge
  check → atomic four-field write. Clock is injectable for deterministic tests.
- `src/aidevos/cli.py`: add the `task transition <TASK-ID> <TARGET-STATE>` subcommand. Argparse
  validates command structure and arity only (two positionals) — no `choices=STATES`. Dispatch to
  `transition_task`; preserve existing `--help`/`--version`/`task validate`.
- Command accepts two positionals: `TASK-ID` matching `^TASK-[0-9]{4}$` and a `TARGET-STATE` token,
  resolving `.ai/tasks/<TASK-ID>/status.yml` relative to CWD. Run from the repository root. No
  Git-root discovery, no `--path`, no batch/`--all`.
- Supported v1 graph (the only permitted edges):
  - `INBOX` → `PLANNING`, `CANCELLED`
  - `PLANNING` → `AWAITING_APPROVAL`, `CANCELLED`
  - `AWAITING_APPROVAL` → `PLANNING`, `APPROVED`, `REJECTED`, `CANCELLED`
  - `APPROVED` → `PLANNING`, `IMPLEMENTING`, `CANCELLED`
  - `IMPLEMENTING` → `PLANNING`, `READY_FOR_REVIEW`, `CANCELLED`
  - `READY_FOR_REVIEW` → `PLANNING`, `IMPLEMENTING`, `APPROVED_FOR_COMMIT`, `REJECTED`, `CANCELLED`
  - `APPROVED_FOR_COMMIT` → `PLANNING`, `IMPLEMENTING`, `REJECTED`, `COMPLETED`, `CANCELLED`
  - `COMPLETED`, `REJECTED`, `CANCELLED` → no transitions (terminal)
- `BLOCKED` is protocol-known but unsupported in v1. A current or target state of `BLOCKED` produces
  exit 2, no write, and a deterministic unsupported-state error
  (`error: state not supported by TASK-0004: BLOCKED`). `BLOCKED` is not modeled as terminal;
  entering/leaving `BLOCKED`, `resume_state`, and blocker metadata are deferred to a future task.
- Canonical status-document validation (before any write): exactly one top-level occurrence of each
  of `schema_version`, `task_id`, `version`, `status`, `updated_by`, `updated_at`; `schema_version`
  is a supported value (`1`); `task_id` equals the CLI `TASK-ID`; `version` is a valid non-negative
  integer; duplicate required keys are rejected; required scalar lines use the canonical
  `key: value` representation. Any violation → `error: invalid status document: <detail>`, exit 2,
  no write.
- Successful write updates exactly `status` (target), `version` (previous + 1), `updated_by`
  (`aidevos_cli`), and `updated_at` (injected UTC time formatted `YYYY-MM-DDTHH:MM:SSZ`), preserving
  all unrelated lines, field ordering, comments, trailing-newline behaviour, original LF/CRLF style,
  and original file permission mode bits.
- Atomic write: validate fully first; write a temp file in the same directory; flush and `os.fsync`;
  `os.replace`; clean up temp files on success or failure; leave the original unchanged after any
  failure. No file locking, no event log.
- Exit-code contract: 0 = supported transition performed; 1 = known/supported states with a
  disallowed edge (includes self-transition and any transition out of a terminal state); 2 = invalid
  usage, invalid `TASK-ID`, missing/unreadable file, invalid status document, unknown target state,
  or `BLOCKED` as current/target.
- `tests/test_task_transition.py` (new) and additions to `tests/test_cli.py` covering the full
  matrix (implementation only — not created in this materialization task).
- This task's own governance records under `.ai/tasks/TASK-0004/**`.

## Non-Goals

`BLOCKED` entry/exit, `resume_state`, and blocker metadata (deferred to a future task). Gate
enforcement of any kind (baseline, scope-diff, evidence, candidate snapshot, review, commit gate) —
TASK-0004 validates graph legality only. Transition history / event log; file locking; reason
capture; actor/role/permission enforcement; approval-artifact verification; evidence generation;
immutable candidate snapshots. Any Git operation (branch, snapshot, commit, push, PR, merge,
release). Automatic agents, multi-agent routing/scheduling, workflow execution, or any general
workflow engine. Daemon, dashboard, database, API, or cloud runtime. Any YAML/JSON parser or new
runtime dependency; a general YAML validator. Git-root discovery or upward path search; a `--path`,
arbitrary-file, or batch/`--all` mode; `--force`, `--dry-run`, interactive confirmation, or
rollback. Validation of `task.md`, `approval.md`, or `plan.md`. Broad refactoring of the existing
CLI or of `task_validation.py`.

## Acceptance Criteria

- [ ] AC-1: A `status.yml` at `status: IMPLEMENTING`, target `READY_FOR_REVIEW`, injected UTC clock
  `2026-07-13T00:00:00Z` → exit 0; stdout `TASK-XXXX: IMPLEMENTING -> READY_FOR_REVIEW`; the file now
  has `status: READY_FOR_REVIEW`, `version` incremented by exactly 1, `updated_by: aidevos_cli`, and
  `updated_at: 2026-07-13T00:00:00Z`.
- [ ] AC-2: After AC-1, every non-updated line is byte-identical (asserted on `schema_version`,
  `task_id`, `resume_state`, `branch`, `baseline_commit`, field ordering, comments, trailing
  newline); original LF/CRLF line-ending style and original file permission mode bits are preserved.
- [ ] AC-3: A supported cancel edge (for example `INBOX` → `CANCELLED`) → exit 0 and the write is
  applied.
- [ ] AC-4: A disallowed edge (`APPROVED` → `COMPLETED`) → exit 1 with a deterministic
  disallowed-transition error; the file is byte-identical.
- [ ] AC-5: A transition from `COMPLETED` to any different supported target state → exit 1 and the
  file is byte-identical. (`COMPLETED` → `BLOCKED` and `COMPLETED` → an unknown token are not exit 1;
  they remain exit 2 by target classification.)
- [ ] AC-6: A self-transition (current `IMPLEMENTING`, target `IMPLEMENTING`) → exit 1; the file is
  byte-identical.
- [ ] AC-7: An unknown target state (for example `WOBBLE`) → exit 2 with
  `error: unknown target state: WOBBLE`; the file is byte-identical.
- [ ] AC-8: `BLOCKED` as target (from a supported current state) → exit 2 with
  `error: state not supported by TASK-0004: BLOCKED`; the file is byte-identical.
- [ ] AC-9: `BLOCKED` as current state (`status: BLOCKED`) → exit 2 with
  `error: state not supported by TASK-0004: BLOCKED`; the file is byte-identical.
- [ ] AC-10: A malformed `TASK-ID` (`foo`, `TASK-3`) → exit 2 with an invalid-Task-ID message and no
  file read.
- [ ] AC-11: A missing status file (`.ai/tasks/TASK-9999/status.yml` absent) → exit 2 with a
  missing-file message, distinct from an exit-1 disallowed edge.
- [ ] AC-12: An invalid status document — each of: a missing required top-level key; a duplicate
  required key (including duplicate `updated_by` or `updated_at`); an unsupported `schema_version`;
  a non-integer or negative `version`; a non-canonical required line — → exit 2 with
  `error: invalid status document: ...` and no write. Additionally, an unrecognized current `status`
  token (for example `status: WOBBLE`) → exit 2, empty stdout, stderr exactly
  `error: invalid status document: unknown current state: WOBBLE`, `status.yml` byte-identical, and
  no temporary file remaining.
- [ ] AC-13: A `status.yml` under `.ai/tasks/TASK-0004/` whose `task_id` is `TASK-9999` → exit 2 and
  the file is byte-identical.
- [ ] AC-14: For every failure case (AC-4 through AC-13), the file's bytes are unchanged (or the file
  remains absent) — asserted via a byte/hash comparison; no temporary file is left behind.
- [ ] AC-15: Success determinism — two independent status files built from identical initial bytes,
  transitioned with the same injected clock and the same target, yield identical stdout, stderr,
  exit code, and identical final file bytes.
- [ ] AC-16: Failure determinism — a failing call invoked twice against the same file yields
  identical stdout, stderr, and exit code, and the file remains unchanged.
- [ ] AC-17: Entry-point parity — `aidevos task transition ...` and `python -m aidevos task
  transition ...` produce identical stdout, stderr, and exit code, exercised over two independent
  repository/status-file copies created from identical initial bytes (never both successful commands
  against one file).
- [ ] AC-18: `pytest -q`, `ruff check .`, `ruff format --check .`, and `mypy src` all pass.
- [ ] AC-19: `[project.dependencies]` in `pyproject.toml` remains empty; no new runtime dependency is
  introduced.
- [ ] AC-20: `aidevos task validate TASK-0004` exits 0 (this task's own `task.md` is a valid §8
  contract).
- [ ] AC-21: A parametrized test covers every ordered pair of the 10 supported current states and
  the 10 supported target states (100 pairs): every edge present in `ALLOWED_TRANSITIONS` succeeds
  with exit 0, and every absent edge fails with exit 1; each successful pair uses an independent
  initial status file, and every failed pair leaves its file byte-identical. `BLOCKED` and unknown
  tokens are excluded from this 10×10 matrix and remain separate exit-2 classification tests.

## Allowed Patterns

- `src/aidevos/task_transition.py`
- `src/aidevos/cli.py`
- `tests/test_task_transition.py`
- `tests/test_cli.py`
- `.ai/tasks/TASK-0004/**`

## Restricted Patterns

- `docs/AI-DevOS-V4.2.1.md` — protocol doc must not be modified.
- `src/aidevos/task_validation.py`, `src/aidevos/__init__.py` (no version bump),
  `src/aidevos/__main__.py`.
- `pyproject.toml` — no dependency additions; `[project.dependencies]` stays empty.
- `tests/fixtures/**` — no new committed fixtures (status fixtures are built inline in `tmp_path`).
- `.ai/tasks/TASK-0001/**`, `.ai/tasks/TASK-0002/**`, `.ai/tasks/TASK-0003/**` — read only, never
  edited.
- All of `.ai/**` except `.ai/tasks/TASK-0004/**`.
- `README.md`, `CLAUDE.md`, `AGENTS.md`, `.gitignore`.
- `.git/**`, `.github/**`.

## Verification Commands

- `pytest -q`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `aidevos task validate TASK-0004` (expect: valid, exit 0)
- `aidevos task validate TASK-0001` (expect: valid, exit 0 — no regression)
- `aidevos --version` (expect: `0.1.0`, exit 0)
- `python -m aidevos task validate TASK-0004` (parity check)

## Dependencies

- Baseline commit: `0b7465d`. Planned implementation branch: `feature/task-0004` (not yet created;
  no branch, worktree, commit, or push is made during planning or this materialization).
  TASK-0001, TASK-0002, and TASK-0003 are COMPLETED on `main`. No task dependencies remain. TASK-0004
  depends only on the existing CLI/argparse and the standard library; it introduces no runtime
  dependency and no new fixture files.

## Risks

- **Self-consistency of the transition-command's own contract** — `aidevos task validate TASK-0004`
  must pass; this `task.md` deliberately follows the TASK-0002/TASK-0003 section schema exactly
  (AC-20).
- **Six validated fields versus four written fields** — the validator requires exactly one top-level
  occurrence of six keys (`schema_version`, `task_id`, `version`, `status`, `updated_by`,
  `updated_at`); the writer updates exactly four (`status`, `version`, `updated_by`, `updated_at`).
  `schema_version` and `task_id` are validated but never modified. All other lines are preserved
  opaquely; matchers are anchored to top-level keys, so a nested or reduced document is preserved
  rather than corrupted.
- **Determinism of `updated_at`** — the production function requires an injected UTC clock so tests
  are byte-deterministic; wall-clock time is used only as the default in real runs. `updated_at` is
  canonicalized to the full `YYYY-MM-DDTHH:MM:SSZ` form (superseding the older date-only records).
- **No-write-on-failure guarantee** — all validation completes before any write; the atomic
  temp-file + `os.replace` path plus temp cleanup ensures the original is byte-identical after every
  failure (AC-14). Proven by capturing file bytes before and after each failure path.
- **Exit-code separation** — disallowed edge (1) must stay distinct from usage/unsupported/invalid
  document (2) so scripts can tell a rejected-but-legal-shape transition from a malformed request.
- **`BLOCKED` scope discipline** — `BLOCKED` is handled only as an exit-2 unsupported-state error,
  never silently; its full lifecycle is a separate future task.
- **Dependency creep** — no YAML/JSON parser is introduced; the canonical validator and line-
  preserving writer are stdlib-only and `[project.dependencies]` stays empty.

## Rollback Notes

- Before approval, an abandoned unapproved materialization may be removed in full (delete
  `.ai/tasks/TASK-0004/`).
- After approval, an implementation rollback restores or deletes implementation source and test
  changes only: revert `src/aidevos/cli.py` and `tests/test_cli.py` to baseline `0b7465d`, and delete
  `src/aidevos/task_transition.py` and `tests/test_task_transition.py`.
- Preserve `.ai/tasks/TASK-0004/**` after approval as governance and audit history. An implementation
  rollback must not delete `task.md`, `plan.md`, `approval.md`, `status.yml`, reviews, or evidence.
- No historical task file, `docs/`, `pyproject.toml`, package version, or Git state is changed by an
  implementation rollback.
