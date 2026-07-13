# Evidence — TASK-0003: Task and Schema Validation

## Verification Commands

The repository `.venv/bin` directory was placed first on `PATH` for the final verification run.

| Command | Exit | Exact result |
|---|---:|---|
| `pytest -q` | 0 | `43 passed in 0.61s` |
| `ruff check .` | 0 | `All checks passed!` |
| `ruff format --check .` | 0 | `6 files already formatted` |
| `mypy src` | 0 | `Success: no issues found in 4 source files` |
| `aidevos task validate TASK-0001` | 0 | `TASK-0001: valid` |
| `aidevos task validate TASK-0002` | 0 | `TASK-0002: valid` |
| `aidevos --version` | 0 | `0.1.0` |
| `aidevos --help` | 0 | Help lists `{task}` and `task  Work with task documents.` |
| `python -m aidevos task validate TASK-0001` | 0 | `TASK-0001: valid` |
| `git diff --check` | 0 | No output |
| `git status --short` | 0 | Inspected; all paths are approved |
| `git diff --stat` | 0 | Inspected; tracked implementation paths are approved |
| `git diff` | 0 | Inspected; changes match the approved contract |

## CLI Exit-Code Evidence

- Exit 0: direct console runs validated TASK-0001 and TASK-0002 and printed only their deterministic
  valid result to stdout.
- Exit 1: `test_invalid_document_is_deterministic_validation_error` runs the console script twice
  against the malformed fixture and asserts exit 1, empty stdout, ordered findings on stderr, no
  traceback, and byte-identical repeated results.
- Exit 2 usage: `test_invalid_task_id_is_usage_error` and
  `test_only_one_positional_task_id_is_accepted` assert exit 2 for an invalid ID, missing/extra
  positional IDs, and `--all`.
- Exit 2 access: `test_missing_task_file_is_access_error`,
  `test_directory_instead_of_file_returns_two`, and the monkeypatched PermissionError/OSError tests
  assert exit 2, empty stdout, a deterministic stderr message, and no traceback.
- The invalid-ID unit tests monkeypatch `Path.read_text` to fail if called, proving invalid IDs do
  not attempt a read.

## Acceptance Criteria

- [x] AC-1: TASK-0001 validates unchanged with exit 0.
- [x] AC-2: TASK-0002 validates unchanged with exit 0.
- [x] AC-3: The complete synthetic fixture validates with exit 0.
- [x] AC-4: Both `[x]` and `[X]` AC forms validate.
- [x] AC-5: Unknown extra section and Metadata field are accepted.
- [x] AC-6: A missing Acceptance Criteria section returns ordered R2/R4 findings and exit 1.
- [x] AC-7: Body text or another heading before the title produces R1 and no traceback.
- [x] AC-8: Invalid Type and Priority values name the value and canonical accepted set.
- [x] AC-9: An empty Requested By value is reported.
- [x] AC-10: A missing Created field is reported.
- [x] AC-11: Malformed AC forms produce R4.
- [x] AC-12: Each empty required list independently produces R5.
- [x] AC-13: A duplicate Goal section produces R2.
- [x] AC-14: A duplicate Type field produces R3 without first/last-wins enum handling.
- [x] AC-15: A differing valid title ID produces R6.
- [x] AC-16: `TASK-3` and `foo` return 2 without reading a file.
- [x] AC-17: Missing TASK-9999 returns 2 with a distinct missing-file message.
- [x] AC-18: Mocked PermissionError and OSError return 2 with empty stdout and no traceback.
- [x] AC-19: Empty and title-less documents produce deterministic findings without traceback.
- [x] AC-20: Repeated malformed validation has byte-identical stdout, stderr, and exit code.
- [x] AC-21: Version is 0.1.0, help lists task, and `python -m` matches the console script.
- [x] AC-22: Pytest, Ruff lint, Ruff format check, and mypy all pass.
- [x] AC-23: `pyproject.toml` is unchanged and `[project.dependencies]` remains `[]`.

All AC-1 through AC-23 are satisfied.

## Complete Changed and Untracked File Inventory

- `README.md`
- `src/aidevos/cli.py`
- `src/aidevos/task_validation.py`
- `tests/test_cli.py`
- `tests/test_task_validation.py`
- `tests/fixtures/tasks/valid.md`
- `tests/fixtures/tasks/checked_ac.md`
- `tests/fixtures/tasks/extra_content.md`
- `tests/fixtures/tasks/malformed.md`
- `.ai/tasks/TASK-0003/task.md`
- `.ai/tasks/TASK-0003/plan.md`
- `.ai/tasks/TASK-0003/approval.md`
- `.ai/tasks/TASK-0003/status.yml`
- `.ai/tasks/TASK-0003/implementation.md`
- `.ai/tasks/TASK-0003/evidence.md`

The first nine paths are approved implementation/documentation/test changes. All governance paths
are confined to the approved `.ai/tasks/TASK-0003/**` area. `task.md`, `plan.md`, and `approval.md`
were pre-existing untracked approved artifacts and were not modified during implementation.

## Boundary Confirmations

- Restricted files and areas were untouched, including `docs/AI-DevOS-V4.2.1.md`,
  `src/aidevos/__init__.py`, `src/aidevos/__main__.py`, `pyproject.toml`, `.ai/schemas/**`,
  `.ai/tasks/TASK-0001/**`, `.ai/tasks/TASK-0002/**`, `.git/**`, and `.github/**`.
- `[project.dependencies]` remains exactly `[]`; no runtime dependency was introduced.
- No commit was created and no push occurred.
