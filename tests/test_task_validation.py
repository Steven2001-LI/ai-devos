from __future__ import annotations

from pathlib import Path

import pytest

from aidevos.task_validation import (
    extract_non_empty_bullets,
    extract_section_body,
    validate_task,
    validate_task_document,
)


FIXTURES = Path(__file__).parent / "fixtures" / "tasks"
VALID_DOCUMENT = (FIXTURES / "valid.md").read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> str:
    assert VALID_DOCUMENT.count(old) == 1
    return VALID_DOCUMENT.replace(old, new)


@pytest.mark.parametrize("task_id", ["TASK-0001", "TASK-0002"])
def test_historical_task_documents_are_valid(task_id: str) -> None:
    path = Path(".ai") / "tasks" / task_id / "task.md"

    assert validate_task_document(task_id, path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("fixture_name", ["valid.md", "checked_ac.md", "extra_content.md"])
def test_valid_synthetic_documents(fixture_name: str) -> None:
    text = (FIXTURES / fixture_name).read_text(encoding="utf-8")

    assert validate_task_document("TASK-0003", text) == []


def test_leading_blank_lines_and_reordered_sections_are_valid() -> None:
    metadata, background = VALID_DOCUMENT.split("## Background", maxsplit=1)
    title, metadata_body = metadata.split("## Metadata", maxsplit=1)
    text = f"\n\n{title}## Background{background}## Metadata{metadata_body}"

    assert validate_task_document("TASK-0003", text) == []


def test_extract_section_body_trims_only_boundary_blank_lines() -> None:
    text = replace_once("Goal text.", "\n  First line.  \n\nSecond line.\n")

    assert extract_section_body(text, "Goal") == "  First line.  \n\nSecond line."
    assert extract_section_body(text, "Unknown") == ""


def test_extract_non_empty_bullets_preserves_source_order() -> None:
    text = replace_once(
        "- `src/**`",
        "Introductory text.\n- `src/**`\n  - nested detail\n-   tests/**   \n-   ",
    )

    assert extract_non_empty_bullets(text, "Allowed Patterns") == [
        "`src/**`",
        "nested detail",
        "tests/**",
    ]
    assert extract_non_empty_bullets(text, "Unknown") == []


@pytest.mark.parametrize("checked", ["x", "X"])
def test_each_checked_acceptance_criterion_form_is_valid(checked: str) -> None:
    text = replace_once("- [ ] AC-1: The task validates.", f"- [{checked}] AC-1: Done.")

    assert validate_task_document("TASK-0003", text) == []


def test_missing_required_section() -> None:
    text = replace_once("## Acceptance Criteria", "## Optional Criteria")

    assert validate_task_document("TASK-0003", text) == [
        "R2: missing required section: Acceptance Criteria",
        "R4: Acceptance Criteria must contain at least one accepted AC item",
    ]


@pytest.mark.parametrize(
    "prefix",
    ["Body text before the title.\n", "## Another heading\n\n"],
)
def test_title_must_be_first_non_empty_line(prefix: str) -> None:
    findings = validate_task_document("TASK-0003", prefix + VALID_DOCUMENT)

    assert findings[0] == ("R1: first non-empty line must match '# TASK-XXXX: <non-empty title>'")
    assert not any(finding.startswith("R6:") for finding in findings)


def test_malformed_fixture_returns_deterministic_findings() -> None:
    text = (FIXTURES / "malformed.md").read_text(encoding="utf-8")

    first = validate_task_document("TASK-0003", text)
    second = validate_task_document("TASK-0003", text)
    assert first == second
    assert first[0] == "R1: first non-empty line must match '# TASK-XXXX: <non-empty title>'"


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        (
            "- Type: feature",
            "- Type: feat",
            "R3: invalid Type 'feat'; expected one of: feature, bugfix, refactor, docs",
        ),
        (
            "- Priority: high",
            "- Priority: urgent",
            "R3: invalid Priority 'urgent'; expected one of: low, medium, high, critical",
        ),
        (
            "- Requested By: Test Owner",
            "- Requested By:",
            "R3: empty required Metadata field: Requested By",
        ),
        (
            "- Created: 2026-07-13\n",
            "",
            "R3: missing required Metadata field: Created",
        ),
    ],
)
def test_metadata_failures(old: str, new: str, expected: str) -> None:
    assert validate_task_document("TASK-0003", replace_once(old, new)) == [expected]


def test_duplicate_required_metadata_field_fails_without_enum_resolution() -> None:
    text = replace_once("- Type: feature", "- Type: feature\n- Type: feat")

    assert validate_task_document("TASK-0003", text) == [
        "R3: duplicate required Metadata field: Type"
    ]


@pytest.mark.parametrize(
    "item",
    [
        "- AC-1: Missing checkbox.",
        "- [y] AC-1: Wrong checkbox.",
        "- [ ] Criterion without an AC number.",
        "- [ ] AC-1:",
    ],
)
def test_acceptance_criteria_requires_an_accepted_item(item: str) -> None:
    text = replace_once("- [ ] AC-1: The task validates.", item)

    assert validate_task_document("TASK-0003", text) == [
        "R4: Acceptance Criteria must contain at least one accepted AC item"
    ]


@pytest.mark.parametrize(
    ("section", "bullet", "expected"),
    [
        ("Allowed Patterns", "- `src/**`", "Allowed Patterns"),
        ("Restricted Patterns", "- `.git/**`", "Restricted Patterns"),
        ("Verification Commands", "- `pytest -q`", "Verification Commands"),
    ],
)
def test_required_lists_must_have_a_non_empty_bullet(
    section: str, bullet: str, expected: str
) -> None:
    del section
    text = replace_once(bullet, "-   ")

    assert validate_task_document("TASK-0003", text) == [
        f"R5: required list must contain a non-empty bullet: {expected}"
    ]


def test_duplicate_required_section() -> None:
    text = VALID_DOCUMENT + "\n## Goal\n\nAnother goal.\n"

    assert validate_task_document("TASK-0003", text) == ["R2: duplicate required section: Goal"]


def test_title_task_id_must_match_argument() -> None:
    text = replace_once("# TASK-0003:", "# TASK-0009:")

    assert validate_task_document("TASK-0003", text) == [
        "R6: title Task ID TASK-0009 does not match requested Task ID TASK-0003"
    ]


def test_empty_document_has_complete_deterministic_findings() -> None:
    expected = [
        "R1: first non-empty line must match '# TASK-XXXX: <non-empty title>'",
        *[
            f"R2: missing required section: {section}"
            for section in (
                "Metadata",
                "Background",
                "Goal",
                "Scope",
                "Non-Goals",
                "Acceptance Criteria",
                "Allowed Patterns",
                "Restricted Patterns",
                "Verification Commands",
                "Dependencies",
                "Risks",
                "Rollback Notes",
            )
        ],
        *[
            f"R3: missing required Metadata field: {field}"
            for field in ("Type", "Priority", "Requested By", "Created")
        ],
        "R4: Acceptance Criteria must contain at least one accepted AC item",
        *[
            f"R5: required list must contain a non-empty bullet: {section}"
            for section in (
                "Allowed Patterns",
                "Restricted Patterns",
                "Verification Commands",
            )
        ],
    ]

    assert validate_task_document("TASK-0003", "") == expected
    assert validate_task_document("TASK-0003", "") == expected


@pytest.mark.parametrize("task_id", ["TASK-3", "foo"])
def test_bad_task_id_returns_two_without_reading(
    task_id: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def unexpected_read(*args: object, **kwargs: object) -> str:
        raise AssertionError("read_text must not be called")

    monkeypatch.setattr(Path, "read_text", unexpected_read)

    assert validate_task(task_id) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"error: invalid Task ID '{task_id}'; expected TASK-XXXX\n"


def test_missing_file_returns_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert validate_task("TASK-9999", cwd=tmp_path) == 2

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "error: task file not found: .ai/tasks/TASK-9999/task.md\n"


def test_directory_instead_of_file_returns_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / ".ai" / "tasks" / "TASK-0003" / "task.md"
    path.mkdir(parents=True)

    assert validate_task("TASK-0003", cwd=tmp_path) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "error: task path is not a file: .ai/tasks/TASK-0003/task.md\n"


@pytest.mark.parametrize("error", [PermissionError(), OSError()])
def test_read_failure_returns_two_without_traceback(
    error: OSError, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failed_read(*args: object, **kwargs: object) -> str:
        raise error

    monkeypatch.setattr(Path, "read_text", failed_read)

    assert validate_task("TASK-0003") == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "error: cannot read task file: .ai/tasks/TASK-0003/task.md\n"
    assert "Traceback" not in output.err


def test_validate_task_prints_valid_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / ".ai" / "tasks" / "TASK-0003" / "task.md"
    path.parent.mkdir(parents=True)
    path.write_text(VALID_DOCUMENT, encoding="utf-8")

    assert validate_task("TASK-0003", cwd=tmp_path) == 0
    output = capsys.readouterr()
    assert output.out == "TASK-0003: valid\n"
    assert output.err == ""


def test_validate_task_prints_ordered_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / ".ai" / "tasks" / "TASK-0003" / "task.md"
    path.parent.mkdir(parents=True)
    path.write_text("", encoding="utf-8")

    assert validate_task("TASK-0003", cwd=tmp_path) == 1
    first = capsys.readouterr()
    assert first.out == ""
    assert first.err.startswith("TASK-0003: invalid\nR1:")
    assert "Traceback" not in first.err

    assert validate_task("TASK-0003", cwd=tmp_path) == 1
    second = capsys.readouterr()
    assert second == first
