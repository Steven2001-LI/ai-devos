# Plan — TASK-0003: Task and Schema Validation

## Current Implementation Summary

Branch `feature/task-0003` off baseline commit `46585f6` (TASK-0001 and TASK-0002 COMPLETED and
merged into `main`); working tree clean before this task's governance artifacts. The CLI in
`src/aidevos/cli.py` exposes only `--version` (and argparse's `--help`): `build_parser()` builds a
single-argument parser and `main()` calls `parse_args()` and returns `0`. There are no subcommands,
no file I/O, and no validation code anywhere. `pyproject.toml` has `dependencies = []`. The only
`task.md` files are `.ai/tasks/TASK-0001/task.md` and `.ai/tasks/TASK-0002/task.md`, both conforming
to AI-DevOS V4.2.1 §8.

## Technical Baseline (approved)

| Decision | Choice | Reason |
|---|---|---|
| Validation approach | Handwritten stdlib (`re`/string) parsing + rules | Subject is Markdown, not JSON/YAML; zero runtime deps; deterministic control over findings. |
| Module layout | Single new module `src/aidevos/task_validation.py` (parse + validate) | Architect directive; no split into multiple production modules for this task. |
| CLI framework | Existing stdlib `argparse` with subparsers | Adds `task` group + `validate` subcommand without a new dependency. |
| Path resolution | `.ai/tasks/<TASK-ID>/task.md` relative to CWD | No Git-root discovery or upward search; run from repo root. |
| Argument contract | One positional `TASK-ID`, `^TASK-[0-9]{4}$` | Exactly one supported invocation; no `--path`, no batch. |
| Runtime dependencies | zero (unchanged) | `[project.dependencies]` stays empty; no `jsonschema`/PyYAML. |
| Schema source | AI-DevOS V4.2.1 §8 Markdown contract, hard-coded v1 | No `.ai/schemas/*.json`; not created this task. |

## Error-Class Boundary: usage/access (exit 2) vs document validation (exit 1)

Two distinct failure surfaces, checked in order; the first that applies decides the exit code:

- **Exit 2 — usage or file access.** Raised before any document parsing:
  - The CLI is invoked incorrectly (unknown subcommand, wrong argument count) — argparse's own
    usage error path.
  - The positional `TASK-ID` does not match `^TASK-[0-9]{4}$`. No file read is attempted.
  - The resolved path `.ai/tasks/<TASK-ID>/task.md` does not exist, is a directory, or is
    unreadable — i.e. reading it raises `FileNotFoundError`, `PermissionError`, `IsADirectoryError`,
    `OSError`, or an equivalent file-access failure. In every such case stdout is empty, a clear
    single-line access-error message is written to stderr, and no traceback is emitted.
- **Exit 1 — document validation failure.** The argument is well-formed and the file was read
  successfully, but one or more contract rules (R1–R6) fail. `<TASK-ID>: invalid` is written
  followed by the ordered findings on stderr.
- **Exit 0 — valid.** The file was read and every rule passed. `<TASK-ID>: valid` is written to
  stdout; stderr is empty.

The boundary rule: reaching the document-validation stage requires a syntactically valid argument
and a successfully read file. Anything that prevents that read is exit 2, never exit 1. The
access-handling boundary is verified by monkeypatching the file-read operation to raise, so the test
does not depend on `chmod` or operating-system permission semantics.

## Validation Contract (rules evaluated by `task_validation.py`)

- **R1 — Title.** Leading blank lines are allowed. The first non-empty line must match
  `# TASK-XXXX: <non-empty title>`. Any body text, another heading, or any other non-empty content
  before the task title makes R1 fail. No broader Markdown parsing behavior is introduced.
- **R2 — Required sections.** Exactly these must each be present once: Metadata, Background, Goal,
  Scope, Non-Goals, Acceptance Criteria, Allowed Patterns, Restricted Patterns, Verification
  Commands, Dependencies, Risks, Rollback Notes. Any order is accepted. Unknown extra sections are
  allowed. A duplicate occurrence of any required section is a failure.
- **R3 — Metadata.** Required non-empty fields `Type`, `Priority`, `Requested By`, `Created`. A
  required field that is absent, present with an empty value, or duplicated is a failure; duplicates
  are reported (neither first-wins nor last-wins). `Type` ∈ {feature, bugfix, refactor, docs};
  `Priority` ∈ {low, medium, high, critical}. `Requested By` and `Created` accept any non-empty
  text. Unknown extra Metadata fields are allowed.
- **R4 — Acceptance Criteria.** The section must contain at least one accepted AC item in one of the
  forms `- [ ] AC-N: <non-empty text>`, `- [x] AC-N: <non-empty text>`, or
  `- [X] AC-N: <non-empty text>`. Validation fails only when the section contains no accepted AC
  item in any of those three forms. No numbering-sequence, order, uniqueness, or semantic-quality
  check.
- **R5 — Required non-empty lists.** `Allowed Patterns`, `Restricted Patterns`, and `Verification
  Commands` each contain at least one non-empty bullet. No glob-correctness or vagueness check.
- **R6 — Task ID consistency.** The Task ID parsed from the R1 title must equal the CLI argument.
  The directory name equals the argument by construction; the title Task ID is the value
  cross-checked. If no valid title Task ID can be parsed (R1 fails), no R6 mismatch finding is
  emitted — only the applicable R1 and other structural findings appear.

Malformed or empty Markdown is a robustness requirement, not a separate rule: an empty file, a
missing title, or otherwise unparseable structure yields deterministic R1/R2 (and any other
applicable) findings and never raises a traceback.

## Deterministic Finding Ordering

Findings are collected during a single parse and then emitted in a fixed total order, independent of
input arrangement, so repeated runs are byte-identical (AC-20):

1. Primary key: rule order **R1 → R2 → R3 → R4 → R5 → R6**.
2. Secondary key within a rule: a fixed canonical order, not source order —
   - R2 Required sections: the canonical section list order above.
   - R3 Metadata: the canonical field order `Type`, `Priority`, `Requested By`, `Created`; for each
     field, missing/empty findings precede duplicate-field findings, both in that canonical order.
   - R5 Required lists: the order Allowed Patterns, Restricted Patterns, Verification Commands.
3. If R1 fails to parse a title Task ID, R6 emits nothing; only the R1 (and any other applicable
   structural) findings are present.
4. Each finding is one line with a stable prefix identifying the rule and the offending detail. No
   timestamps, file-system paths beyond the target, or other nondeterministic content appear in
   output.

## Minimal Implementation Path

1. `task_validation.py`: a pure function `validate_task_document(task_id, text) -> list[str]`
   (ordered findings; empty list = valid) plus a small internal parser that splits the document into
   the title (first non-empty line), `## `-delimited sections, and Metadata `- Key: value` bullets.
   No file I/O in the pure core.
2. `task_validation.py`: a thin `validate_task(task_id, cwd) -> int` that validates the argument
   format and resolves `.ai/tasks/<TASK-ID>/task.md` relative to `cwd`, wraps the file read to map
   `FileNotFoundError`/`PermissionError`/`IsADirectoryError`/`OSError` to a clear exit-2 stderr
   message (empty stdout, no traceback), reads the file, calls the pure function, prints results,
   and returns 0/1.
3. `cli.py`: add subparsers, register `task validate <TASK-ID>`, and dispatch from `main()`
   returning the handler's exit code; keep `--version`/`--help` intact.
4. Fixtures under `tests/fixtures/tasks/` covering each positive and negative case.
5. Tests in `tests/test_task_validation.py` (unit, pure function + monkeypatched read) and
   `tests/test_cli.py` (subprocess, exit codes and `--help`).
6. `README.md`: add the command example and exit-code description.
7. Run the tooling gate; hand off for review. No commit or push.

## Expected Change Areas

- `src/aidevos/cli.py`
- `src/aidevos/task_validation.py` (new)
- `tests/test_cli.py`
- `tests/test_task_validation.py` (new)
- `tests/fixtures/tasks/**` (new)
- `README.md`
- `.ai/tasks/TASK-0003/**` (governance records)

## Test Strategy

TDD (§29). Write the failing unit tests for `validate_task_document` first, then the CLI subprocess
tests, then implement. Unit tests exercise the pure function against fixture strings; the
unreadable-file boundary is tested by monkeypatching the file-read operation to raise
`PermissionError`/`OSError` (no reliance on `chmod` or OS permission semantics). CLI tests invoke
the installed console script via `subprocess` and assert exit codes and messages. The two historical
`task.md` files are loaded read-only as golden positive fixtures.

### Positive / Negative Test Matrix

| ID | Case | Input | Expected | AC |
|---|---|---|---|---|
| P1 | Live TASK-0001 valid | `.ai/tasks/TASK-0001/task.md` | exit 0, `valid` | AC-1 |
| P2 | Live TASK-0002 valid | `.ai/tasks/TASK-0002/task.md` | exit 0, `valid` | AC-2 |
| P3 | Synthetic valid fixture | all rules pass | exit 0 | AC-3 |
| P4 | Checked AC forms `[x]`/`[X]` | valid otherwise | exit 0 | AC-4 |
| P5 | Unknown extra section + extra Metadata field | valid otherwise | exit 0 | AC-5 |
| N1 | Missing required section (R2) | no `## Acceptance Criteria` | exit 1, names section | AC-6 |
| N2 | Title not first non-empty line (R1) | body text/another heading before title | exit 1, title finding, no traceback | AC-7 |
| N3 | Invalid `Type` enum (R3) | `Type: feat` | exit 1, names value + set | AC-8 |
| N4 | Invalid `Priority` enum (R3) | out-of-enum `Priority` | exit 1 | AC-8 |
| N5 | Empty Metadata value (R3) | `Requested By:` empty | exit 1, names empty field | AC-9 |
| N6 | Missing Metadata field entirely (R3) | `Created` omitted | exit 1, names missing field | AC-10 |
| N7 | No accepted AC item (R4) | AC section has no `[ ]`/`[x]`/`[X]` `AC-N` item | exit 1 | AC-11 |
| N8 | Empty required list (R5) | empty `## Allowed Patterns` (and each other) | exit 1 | AC-12 |
| N9 | Duplicate required section (R2) | `## Goal` twice | exit 1, duplicate finding | AC-13 |
| N10 | Duplicate Metadata field (R3) | `Type` twice | exit 1, duplicate finding, no first/last-wins | AC-14 |
| N11 | Task ID mismatch (R6) | arg `TASK-0003`, title `TASK-0009` | exit 1, mismatch finding | AC-15 |
| N12 | Empty document | zero-length file | exit 1, deterministic findings, no traceback | AC-19 |
| U1 | Bad argument format | `TASK-3`, `foo` | exit 2, no file read | AC-16 |
| U2 | Missing file/dir | `TASK-9999` | exit 2, missing-file message | AC-17 |
| U3 | Unreadable file (mocked) | monkeypatch read → `PermissionError`/`OSError` | exit 2, stderr access message, empty stdout, no traceback | AC-18 |
| D1 | Determinism | run N12 twice | byte-identical stdout/stderr/exit | AC-20 |
| R1 | No regression | `--version`, `--help` lists `task`, `python -m` parity | exit 0 | AC-21 |
| G1 | Tooling gate | `pytest -q`, `ruff check .`, `ruff format --check .`, `mypy src` | all pass | AC-22 |
| G2 | Zero deps | `[project.dependencies]` empty | unchanged | AC-23 |

## Risk Handling

See `task.md` Risks. Key controls: the two live files are golden positive fixtures that must pass
unchanged; findings and their sort order are fixed (R1 → R6 ordering above) and asserted
byte-for-byte; the usage/access-vs-validation boundary is tested with distinct exit-2 (bad argument,
missing file, mocked unreadable read) and exit-1 cases; strict Allowed Patterns keep the diff to the
approved files plus this task's governance records; the validator is stdlib-only so
`[project.dependencies]` stays empty.

## Alternatives Considered

- JSON Schema / `.ai/schemas/*.json` with `jsonschema` — rejected: the subject is Markdown, it adds
  a runtime dependency, and the schema-file layer belongs to a later `init`/meta-governance task.
- Pydantic or a YAML schema library — rejected: heavy dependency for a dozen deterministic checks;
  violates the zero-dependency policy.
- Splitting parsing and validation into separate production modules — rejected by Architect
  directive; both live in `src/aidevos/task_validation.py` for this task.
- Git-root discovery so the command works from any subdirectory — rejected: out of scope; resolution
  is CWD-relative and the command is documented to run from the repository root.
