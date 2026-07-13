# TASK-0003: Task and Schema Validation

## Metadata

- Type: feature
- Priority: high
- Requested By: Human Owner
- Created: 2026-07-13

## Background

TASK-0001 established the installable `aidevos` CLI skeleton (`--help` / `--version` only) and
TASK-0002 aligned product positioning. AI-DevOS V4.2.1 §8 defines the `task.md` Task Schema, §24.2
names `aidevos task validate TASK-XXXX`, and §35 places task-schema validation in the first CLI
phase; TASK-0002 records this as roadmap #2.

Task contracts are the trust anchor of every later gate — scope-diff enforcement, candidate
snapshots, evidence, and the commit gate all consume fields defined by `task.md`. Today those
contracts are authored entirely by hand with no machine check: a missing required section, an
invalid `Type`, a required Metadata field that is absent or empty, an empty pattern list, a
duplicate section or field, or a title whose Task ID disagrees with its directory is caught only by
human review. TASK-0003 adds the first deterministic, tool-enforced answer to one question — is this
`task.md` structurally well-formed and internally consistent enough to be trusted as input — and
nothing more.

No `.ai/schemas/*.json` files exist and none are created here. Validation is performed directly
against the §8 Markdown contract with the standard library and zero runtime dependencies.

## Goal

Add a deterministic `aidevos task validate <TASK-ID>` command that validates a single
`.ai/tasks/<TASK-ID>/task.md` against an explicit structural-plus-consistency contract, printing a
pass/fail result and exiting with a stable, scriptable status code (0 valid, 1 document validation
failure, 2 usage or file-access error). Parsing and validation are handwritten in one new module,
`src/aidevos/task_validation.py`; CLI wiring stays in `src/aidevos/cli.py`. No new runtime
dependency is added.

## Scope

- `src/aidevos/cli.py`: add the `task` command group and its `validate` subcommand via argparse
  subparsers; `main()` dispatches to the handler and returns its exit code. The existing `--help`
  and `--version` behavior is preserved.
- `src/aidevos/task_validation.py` (new): stdlib-only `task.md` parsing and evaluation of the
  validation contract (rules R1–R6 below), returning an ordered list of findings. Parsing and
  validation live in this single production module.
- The command accepts exactly one positional `TASK-ID` argument matching `^TASK-[0-9]{4}$` and
  resolves the target file as `.ai/tasks/<TASK-ID>/task.md` relative to the current working
  directory. It is intended to run from the repository root. No Git-root discovery, no upward
  search, no `--path`, no batch or `--all` mode.
- Exit-code contract: 0 = valid task; 1 = task document validation failure; 2 = invalid CLI usage,
  invalid `TASK-ID` argument, missing file, or unreadable/failed file read.
- Validation contract (R1–R6), evaluated against the Markdown document:
  - **R1 — Title.** Leading blank lines are allowed. The first non-empty line must match
    `# TASK-XXXX: <non-empty title>`. Any body text, another heading, or any other non-empty
    content appearing before the task title makes R1 fail. No broader Markdown parsing behavior is
    introduced.
  - **R2 — Required sections.** Exactly these must each be present once, in any order, with unknown
    extra sections allowed; a duplicate occurrence of any required section is a failure: Metadata,
    Background, Goal, Scope, Non-Goals, Acceptance Criteria, Allowed Patterns, Restricted Patterns,
    Verification Commands, Dependencies, Risks, Rollback Notes.
  - **R3 — Metadata.** Required fields `Type`, `Priority`, `Requested By`, `Created` must each be
    present and non-empty; `Type` ∈ {feature, bugfix, refactor, docs}; `Priority` ∈ {low, medium,
    high, critical}; `Requested By` and `Created` accept any non-empty text. Unknown extra Metadata
    fields are allowed. A required Metadata field that is absent, that is present with an empty
    value, or that occurs more than once (neither first-wins nor last-wins) is a failure.
  - **R4 — Acceptance Criteria.** The section must contain at least one accepted AC item in one of
    the forms `- [ ] AC-N: <non-empty text>`, `- [x] AC-N: <non-empty text>`, or
    `- [X] AC-N: <non-empty text>`. Validation fails only when the section contains no accepted AC
    item in any of those three forms. No numbering-sequence, order, uniqueness, or semantic-quality
    check.
  - **R5 — Required non-empty lists.** `Allowed Patterns`, `Restricted Patterns`, and `Verification
    Commands` must each contain at least one non-empty bullet. No glob-correctness or vagueness
    check.
  - **R6 — Task ID consistency.** The Task ID parsed from the R1 title must equal the CLI argument.
    Because the path is built from the argument, the directory name equals the argument by
    construction; the title Task ID is the value cross-checked. If no valid title Task ID can be
    parsed (R1 fails), no R6 mismatch finding is emitted — only the applicable R1 and other
    structural findings appear.
  - Malformed or empty Markdown is a robustness requirement, not a separate rule: an empty file, a
    missing title, or otherwise unparseable structure yields deterministic R1/R2 (and any other
    applicable) findings and never raises a traceback.
- `tests/test_task_validation.py` (new) and additions to `tests/test_cli.py` covering the full
  positive and negative matrix in `plan.md`.
- `tests/fixtures/tasks/*.md` (new): valid and invalid `task.md` fixtures.
- `README.md`: a concise `aidevos task validate` command example and the exit-code description.
- This task's own governance records under `.ai/tasks/TASK-0003/**`.

## Non-Goals

Lifecycle state transitions and the state machine; transition authorization; automatic file
mutation or repair; scope-versus-git-diff enforcement; Git snapshot / candidate tree creation;
evidence generation; review approval; commit, push, merge, or release automation; daemon,
dashboard, database, plugin, or cloud behavior; multi-agent routing/scheduling. Git-root discovery
or upward path search. A `--path`, arbitrary-file, or batch/`--all` mode. Validation of
`status.yml`, `approval.md`, or `plan.md`. JSON Schema, `.ai/schemas/*.json`, `aidevos init`, or the
generic `.ai/` scaffold. Any YAML/JSON parser or new runtime dependency. Semantic-quality judgement
of Acceptance Criteria, AC numbering/order/uniqueness checks, verification-command vagueness checks,
or glob correctness against the repository tree. Broad refactoring of the existing CLI.

## Acceptance Criteria

- [ ] AC-1: `aidevos task validate TASK-0001` prints a valid result and exits 0 without modifying
  `.ai/tasks/TASK-0001/task.md`.
- [ ] AC-2: `aidevos task validate TASK-0002` prints a valid result and exits 0 without modifying
  `.ai/tasks/TASK-0002/task.md`.
- [ ] AC-3: A fixture `task.md` satisfying every rule exits 0.
- [ ] AC-4: A fixture whose Acceptance Criteria uses the checked forms `- [x] AC-1: ...` or
  `- [X] AC-1: ...` and is otherwise valid exits 0.
- [ ] AC-5: A fixture with an unknown extra section and an unknown extra Metadata field, otherwise
  valid, exits 0.
- [ ] AC-6: A fixture missing the `## Acceptance Criteria` section exits 1 and the output names the
  missing required section (R2).
- [ ] AC-7: A fixture whose first non-empty line is not `# TASK-XXXX: <non-empty title>` — including
  a fixture with body text or another heading before the title — exits 1 with a deterministic title
  finding and no traceback (R1).
- [ ] AC-8: A fixture with `Type: feat` exits 1 and names the invalid `Type` value and the accepted
  set; a fixture with an out-of-enum `Priority` likewise exits 1 (R3).
- [ ] AC-9: A fixture whose Metadata field has an empty value (e.g. `Requested By:` with no text)
  exits 1 and names the empty required Metadata field (R3).
- [ ] AC-10: A fixture whose Metadata section omits a required field entirely (e.g. `Created` absent)
  exits 1 and the output names the missing required Metadata field (R3).
- [ ] AC-11: A fixture whose `## Acceptance Criteria` section contains no accepted AC item — none of
  `- [ ] AC-N: <non-empty text>`, `- [x] AC-N: <non-empty text>`, or `- [X] AC-N: <non-empty text>`
  — exits 1 (R4).
- [ ] AC-12: A fixture with an empty `## Allowed Patterns` (and, in separate fixtures, empty
  `## Restricted Patterns` and empty `## Verification Commands`) exits 1 (R5).
- [ ] AC-13: A fixture containing a required section twice (e.g. `## Goal` duplicated) exits 1 and
  reports the duplicate required section (R2).
- [ ] AC-14: A fixture containing a required Metadata field twice (e.g. `Type` duplicated) exits 1
  and reports the duplicate Metadata field; the validator applies neither first-wins nor last-wins
  (R3).
- [ ] AC-15: A fixture whose R1 title Task ID differs from the CLI argument (argument `TASK-0003`,
  title `# TASK-0009: ...`) exits 1 with a Task-ID-mismatch finding (R6).
- [ ] AC-16: `aidevos task validate TASK-3` and `aidevos task validate foo` exit 2 as usage errors
  and do not attempt to read any file.
- [ ] AC-17: `aidevos task validate TASK-9999` with no such directory or file exits 2 with a
  missing-file message, distinct from an exit-1 validation failure.
- [ ] AC-18: When reading the resolved `task.md` raises `PermissionError`, `OSError`, or an
  equivalent file-access failure, the command returns exit 2, stderr contains a clear access-error
  message, stdout is empty, and no traceback is emitted.
- [ ] AC-19: An empty or title-less `task.md` produces deterministic findings with no traceback and
  exits 1.
- [ ] AC-20: Running the same invalid fixture twice produces byte-identical stdout, stderr, and exit
  code.
- [ ] AC-21: `aidevos --version` prints `0.1.0` and exits 0; `aidevos --help` exits 0 and lists the
  `task` command; `python -m aidevos task validate TASK-0001` matches the console-script result.
- [ ] AC-22: `pytest -q`, `ruff check .`, `ruff format --check .`, and `mypy src` all pass.
- [ ] AC-23: `[project.dependencies]` in `pyproject.toml` remains empty; no new runtime dependency
  is introduced.

## Allowed Patterns

- `src/aidevos/cli.py`
- `src/aidevos/task_validation.py`
- `tests/test_cli.py`
- `tests/test_task_validation.py`
- `tests/fixtures/tasks/**`
- `README.md`
- `.ai/tasks/TASK-0003/**`

## Restricted Patterns

- `docs/AI-DevOS-V4.2.1.md` — protocol doc must not be modified.
- `src/aidevos/__init__.py` (no version bump), `src/aidevos/__main__.py`.
- `pyproject.toml` — no dependency additions; `[project.dependencies]` stays empty.
- `.ai/schemas/**` — not created in this task.
- `.ai/tasks/TASK-0001/**`, `.ai/tasks/TASK-0002/**` — read as fixtures only, never edited.
- All of `.ai/**` except `.ai/tasks/TASK-0003/**`.
- `.git/**`, `.github/**`.

## Verification Commands

- `pytest -q`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `aidevos task validate TASK-0001` (expect: valid, exit 0)
- `aidevos task validate TASK-0002` (expect: valid, exit 0)
- `aidevos --version` (expect: `0.1.0`, exit 0)
- `aidevos --help` (expect: lists `task`, exit 0)
- `python -m aidevos task validate TASK-0001` (parity check)

## Dependencies

- Baseline commit: `46585f6`. Branch: `feature/task-0003`. TASK-0001 and TASK-0002 are COMPLETED on
  `main`. No task dependencies remain. TASK-0003 does not depend on `aidevos init` or `.ai/schemas/`;
  it validates the §8 Markdown contract directly.

## Risks

- **Over-strict parsing rejecting the live files** — the two historical `task.md` files are the
  golden fixtures (AC-1, AC-2) and must pass unchanged; heading and Metadata matching tolerate
  trailing whitespace and blank lines, and R1 allows leading blank lines before the title. Section
  matching uses `^##\s+<Name>\s*$`; extra sections/fields are ignored; duplicates of required
  sections/fields are rejected.
- **Error-message and ordering stability** — findings and their sort order are fixed now (AC-20) so
  later tooling and tests can depend on them; ordering is defined in `plan.md`.
- **CWD-relative resolution** — running from a subdirectory yields a missing-file exit 2, not a
  false validation failure. `README.md` documents that the command runs from the repository root.
- **Exit-code collision** — validation failure (1) and usage/access error (2) must stay distinct so
  scripts can tell an invalid task from an unreadable or missing one; the unreadable-read path
  (AC-18) is exercised via a controlled mock of the file read, not OS permission semantics.
- **Dependency creep** — the temptation to reach for `jsonschema`/PyYAML is rejected; the validator
  is stdlib-only and `[project.dependencies]` stays empty.
- **Task schema versioning** — `task.md` carries no version marker; TASK-0003 hard-codes the §8 v1
  contract, and any future schema change is a separate meta-governance task.

## Rollback Notes

All changes are additive except the `src/aidevos/cli.py`, `tests/test_cli.py`, and `README.md`
edits. Rollback = revert those three files to baseline `46585f6` and delete
`src/aidevos/task_validation.py`, `tests/test_task_validation.py`, `tests/fixtures/tasks/`, and
`.ai/tasks/TASK-0003/`. No historical task file, `docs/`, `pyproject.toml`, or package version is
changed.
