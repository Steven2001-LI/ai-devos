# Plan — TASK-0004: Declarative Task State Transitions

## Current Implementation Summary (repository findings)

Planned implementation branch `feature/task-0004` off baseline commit `0b7465d` (TASK-0001,
TASK-0002, TASK-0003 COMPLETED on `main`; working tree clean before this task's governance
artifacts). `src/aidevos/cli.py` exposes `--version`/`--help` and `task validate <TASK-ID>` via
argparse subparsers; `main()` returns the handler's exit code, else `2`.
`src/aidevos/task_validation.py` implements the §8 `task.md` validator and establishes the house
conventions this task reuses: `TASK_ID_PATTERN = ^TASK-[0-9]{4}$`; exit codes 0/1/2 (success /
domain failure / usage-access); success → stdout, errors → stderr, never a traceback; determinism;
and an injectable `cwd` for hermetic tests. `pyproject.toml` has `dependencies = []`; no YAML/JSON
library is used anywhere. `status.yml` for TASK-0001..0003 is a flat, unquoted, top-level
`key: value` document (`schema_version, task_id, version, status, resume_state, branch,
baseline_commit, updated_by, updated_at`) — a reduced subset of §7.9; those files are hand-authored
static records pending exactly this CLI. §10.3 deletes `COMMITTED`/`PUSHED`/`MERGED`/`RELEASED`/
`ROLLED_BACK` from the MVP; there is no `ARCHIVED` state, so `COMPLETED` is the correct terminal.

## Exact CLI Contract

- Invocation: `aidevos task transition <TASK-ID> <TARGET-STATE>` (and `python -m aidevos ...`).
- Positionals: `task_id` (metavar `TASK-ID`) and `target_state` (metavar `TARGET-STATE`), both
  plain strings. Argparse validates structure/arity only (two positionals) — **no `choices=STATES`**;
  all state-token classification is done by the domain function so the direct-call and CLI paths
  share identical semantics.
- Path resolution: `.ai/tasks/<TASK-ID>/status.yml` relative to `cwd` (`Path.cwd()` default;
  injectable `cwd` for tests). No Git-root discovery, no `--path`.
- Success (stdout): `TASK-XXXX: <FROM> -> <TARGET>`, exit 0. Failure (stderr): `error: <reason>`,
  no stdout, no traceback.
- Modifies only `status.yml`. No `--dry-run`/`--force`/interactive/batch/rollback.

## Supported and Known State Definitions

- `SUPPORTED_STATES` (tuple): `INBOX, PLANNING, AWAITING_APPROVAL, APPROVED, IMPLEMENTING,
  READY_FOR_REVIEW, APPROVED_FOR_COMMIT, COMPLETED, REJECTED, CANCELLED`.
- `KNOWN_STATES` = `SUPPORTED_STATES + ("BLOCKED",)`. `BLOCKED` is known to the protocol but
  unsupported by TASK-0004 v1.
- `ALLOWED_TRANSITIONS: dict[str, frozenset[str]]` maps each supported state to its permitted
  successors; terminal states map to an empty frozenset. `BLOCKED` is neither a key nor a value —
  it is not modeled as active or terminal.

## Complete Transition Table

| From | Allowed targets | Terminal? |
|---|---|---|
| `INBOX` | `PLANNING`, `CANCELLED` | No |
| `PLANNING` | `AWAITING_APPROVAL`, `CANCELLED` | No |
| `AWAITING_APPROVAL` | `PLANNING`, `APPROVED`, `REJECTED`, `CANCELLED` | No |
| `APPROVED` | `PLANNING`, `IMPLEMENTING`, `CANCELLED` | No |
| `IMPLEMENTING` | `PLANNING`, `READY_FOR_REVIEW`, `CANCELLED` | No |
| `READY_FOR_REVIEW` | `PLANNING`, `IMPLEMENTING`, `APPROVED_FOR_COMMIT`, `REJECTED`, `CANCELLED` | No |
| `APPROVED_FOR_COMMIT` | `PLANNING`, `IMPLEMENTING`, `REJECTED`, `COMPLETED`, `CANCELLED` | No |
| `COMPLETED` | — (none) | Yes |
| `REJECTED` | — (none) | Yes |
| `CANCELLED` | — (none) | Yes |
| `BLOCKED` | unsupported in v1 → exit 2, no write | not modeled |

## Canonical Document Validation Rules

Validate the current AI-DevOS canonical `status.yml` format (not general YAML). Before any write:

1. Exactly one top-level occurrence of each of `schema_version`, `task_id`, `version`, `status`,
   `updated_by`, `updated_at`. Missing or duplicate any of these (including `updated_by` /
   `updated_at`) → invalid status document.
2. `schema_version` is a supported value (`1`).
3. `task_id` equals the CLI `TASK-ID` argument.
4. `version` is a valid non-negative integer.
5. Required scalar lines use the canonical `key: value` representation (top-level, unquoted scalar).

Any violation → `error: invalid status document: <detail>`, exit 2, no write. The term "general YAML
parser/validation" is not used; unrelated lines are preserved opaquely.

## Deterministic Error Classification

Checked in order; the first that applies decides the outcome (no write on any non-zero exit):

- `TASK-ID` fails `^TASK-[0-9]{4}$` → exit 2 (`error: invalid Task ID ...`), no file read.
- Status file missing / directory / unreadable → exit 2 (`error: status file not found: ...` or
  `error: cannot read ...`), no traceback.
- Canonical document validation fails (including `task_id` mismatch) → exit 2
  (`error: invalid status document: ...`).
- Current `status` is `BLOCKED`, or `TARGET-STATE` is `BLOCKED` → exit 2
  (`error: state not supported by TASK-0004: BLOCKED`).
- `TARGET-STATE` is not in `KNOWN_STATES` → exit 2 (`error: unknown target state: <TOKEN>`).
- Current `status` is not in `KNOWN_STATES` (unrecognized token, for example `WOBBLE`; `BLOCKED` is
  intercepted by the earlier rule) → exit 2, empty stdout, stderr exactly
  `error: invalid status document: unknown current state: <TOKEN>`, no write.
- Both states supported but `target not in ALLOWED_TRANSITIONS[current]` (includes self-transition
  and any transition out of a terminal state) → exit 1 (`error: disallowed transition: <FROM> ->
  <TARGET>`).
- Otherwise → perform, exit 0.

## Atomic-Write Algorithm

1. Complete all validation (ID, read, document validation, state classification, edge check) before
   any write.
2. Compute the new content by line-preserving substitution of exactly `status`, `version`,
   `updated_by`, `updated_at`.
3. Create a temporary file in the same directory as `status.yml`.
4. Write the new content; `flush`; `os.fsync` the temp file descriptor.
5. `os.replace(temp, status.yml)` (atomic on POSIX).
6. Clean up the temporary file on success or failure (`try/finally`, best-effort unlink).
7. On any failure, make no replacement — the original `status.yml` remains byte-identical.

No file locking and no event log. Extended attributes and directory `fsync` are not required.

## Field / Newline / Mode Preservation Requirements

A successful replacement preserves: every unrelated content line (byte-for-byte); field ordering;
comments; trailing-newline behaviour; the original LF or CRLF line-ending style; and the original
file permission mode bits. Only the four dynamic fields change: `status` → target, `version` →
previous + 1, `updated_by` → `aidevos_cli`, `updated_at` → injected UTC time formatted
`YYYY-MM-DDTHH:MM:SSZ`. The production function accepts an injected clock (default
`datetime.now(timezone.utc)`); tests pass a fixed instant.

## Test Matrix (for the implementation task)

| ID | Case | Expected | AC |
|---|---|---|---|
| P1 | Permitted `IMPLEMENTING`→`READY_FOR_REVIEW`, fixed clock | exit 0; four fields updated | AC-1 |
| P2 | Preservation of unrelated lines / order / comments / newline / LF-CRLF / mode | unchanged | AC-2 |
| P3 | Cancel edge `INBOX`→`CANCELLED` | exit 0, write applied | AC-3 |
| N1 | Disallowed `APPROVED`→`COMPLETED` | exit 1, byte-identical | AC-4 |
| N2 | `COMPLETED`→any different supported target | exit 1, byte-identical (`COMPLETED`→`BLOCKED`/unknown-token remain exit 2 by target classification) | AC-5 |
| N3 | Self-transition `IMPLEMENTING`→`IMPLEMENTING` | exit 1, byte-identical | AC-6 |
| N4 | Unknown target `WOBBLE` | exit 2, byte-identical | AC-7 |
| N5 | `BLOCKED` as target | exit 2 unsupported-state error, byte-identical | AC-8 |
| N6 | `BLOCKED` as current | exit 2 unsupported-state error, byte-identical | AC-9 |
| N7 | Malformed `TASK-ID` (`foo`, `TASK-3`) | exit 2, no read | AC-10 |
| N8 | Missing status file | exit 2 missing-file message | AC-11 |
| N9 | Invalid document (missing/dup key incl `updated_by`/`updated_at`; bad `schema_version`; bad `version`; non-canonical line) | exit 2, no write | AC-12 |
| N10 | `task_id` mismatch (`TASK-9999` under `TASK-0004/`) | exit 2, byte-identical | AC-13 |
| N11 | Unknown current state (`status: WOBBLE`) | exit 2, stderr exactly `error: invalid status document: unknown current state: WOBBLE`, empty stdout, byte-identical, no temp left | AC-12 |
| G1 | No write on any failure (bytes unchanged, no temp left) | verified | AC-14 |
| D1 | Success determinism — two independent files, same clock/target | identical output + final bytes | AC-15 |
| D2 | Failure determinism — repeated call, same file | identical output, unchanged | AC-16 |
| R1 | Entry-point parity over two independent copies | identical output | AC-17 |
| T1 | Tooling gate `pytest`/`ruff`/`ruff format`/`mypy` | all pass | AC-18 |
| T2 | Zero runtime deps | `[project.dependencies]` empty | AC-19 |
| S1 | `aidevos task validate TASK-0004` | exit 0 | AC-20 |
| M1 | Exhaustive 10×10 supported-state matrix (100 ordered pairs; excludes `BLOCKED`/unknown tokens) | present edge → exit 0 (independent initial file each); absent edge → exit 1, byte-identical | AC-21 |

Status-file fixtures are built inline in `tmp_path`; no new committed fixtures. Success determinism
and entry-point parity use two independent files from identical initial bytes (a successful
transition is never invoked twice on one file, because the first write changes the state); failure
cases may reuse one file because no write occurs.

## Implementation Sequence (TDD, for the implementation task)

1. Write failing unit tests for `transition_task` (state table, classification, document validation,
   atomic write, preservation, no-write-on-failure, determinism) against inline `tmp_path` fixtures.
2. Write failing CLI subprocess tests (success, disallowed, unknown/`BLOCKED` target, malformed id,
   entry-point parity over two copies).
3. Implement `src/aidevos/task_transition.py`: constants, canonical validator, `transition_task`,
   atomic-write helper.
4. Wire `task transition` into `src/aidevos/cli.py`.
5. Run the tooling gate; hand off for review. No commit or push.

## Fixed Architect Decisions

Supported v1 graph as tabulated above. `BLOCKED` known-but-unsupported → exit 2, no write,
deterministic unsupported-state error, not terminal (resume/blocker deferred). Canonical status-
document validation (six required keys incl. `updated_by`/`updated_at`; `task_id` match; non-negative
integer `version`; supported `schema_version`; canonical representation) — not general YAML. Success
updates `status`, `version+1`, `updated_by=aidevos_cli`, `updated_at`=injected UTC `YYYY-MM-DDTHH:MM:SSZ`.
Preserve unrelated content, ordering, comments, trailing newline, LF/CRLF, and mode bits; clean up
temp files. Self-transition → exit 1, no write. Unknown target → exit 2. Disallowed supported edge →
exit 1. Success → exit 0. No `choices=STATES`; direct function and CLI share semantics. Determinism
and parity tests use two independent copies from identical bytes. Deferred: event log, file locking,
reason capture, gate enforcement. Zero new runtime dependencies; no Git operations; no automatic
agents; no workflow engine; no unrelated refactoring.

## Scope-Creep Check

TASK-0004 remains a repository-native, local, pre-commit governance capability: one CLI verb that
reads and atomically rewrites a single local `status.yml` under `.ai/tasks/`, driven by a static data
table and a fixed canonical-format validator. It adds no daemon, service, network, database,
scheduler, agent routing, gate execution, event log, lock, or Git/commit action; introduces no new
runtime dependency; and touches only `status.yml`. It is strictly roadmap step #3 and does not drift
toward a workflow-orchestration platform.

## Alternatives Considered

- Full YAML parse/reserialize (PyYAML/ruamel) — rejected: adds a runtime dependency barred by the
  zero-dependency policy and the earlier non-goals; risks reordering/reflow. Line-preserving
  substitution over the canonical format is deterministic and stdlib-only.
- `argparse choices=STATES` for the target — rejected by Architect: argparse validates arity/structure
  only; the domain function owns state classification so CLI and direct-call semantics are identical.
- Implementing `BLOCKED`/`resume_state`/blocker metadata now — rejected: data-dependent and nested;
  deferred to a separate future task. Handled here only as an exit-2 unsupported-state error.
- File locking / event log — rejected for v1: a local single-user CLI has no demonstrated concurrent-
  writer need; `os.replace` provides atomicity.
