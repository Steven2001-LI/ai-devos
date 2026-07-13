from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import aidevos


FIXTURES = Path(__file__).parent / "fixtures" / "tasks"


def write_status(root: Path, status: str = "IMPLEMENTING") -> Path:
    path = root / ".ai" / "tasks" / "TASK-0004" / "status.yml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(
            (
                "schema_version: 1",
                "task_id: TASK-0004",
                "version: 3",
                f"status: {status}",
                "resume_state: null",
                "updated_by: test",
                "updated_at: 2026-07-13T00:00:00Z",
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


def test_version() -> None:
    result = subprocess.run(
        ["aidevos", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == aidevos.__version__


def test_help() -> None:
    result = subprocess.run(
        ["aidevos", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "usage: aidevos" in result.stdout
    assert "task" in result.stdout


def test_historical_tasks_validate_with_console_script() -> None:
    for task_id in ("TASK-0001", "TASK-0002"):
        result = subprocess.run(
            ["aidevos", "task", "validate", task_id],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout == f"{task_id}: valid\n"
        assert result.stderr == ""


def test_python_module_validation_matches_console_script() -> None:
    command = ["task", "validate", "TASK-0001"]
    console = subprocess.run(["aidevos", *command], check=False, capture_output=True, text=True)
    module = subprocess.run(
        ["python", "-m", "aidevos", *command],
        check=False,
        capture_output=True,
        text=True,
    )

    assert module.returncode == console.returncode
    assert module.stdout == console.stdout
    assert module.stderr == console.stderr


def test_invalid_task_id_is_usage_error() -> None:
    result = subprocess.run(
        ["aidevos", "task", "validate", "foo"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: invalid Task ID 'foo'; expected TASK-XXXX\n"


def test_only_one_positional_task_id_is_accepted() -> None:
    for arguments in (
        ["task", "validate"],
        ["task", "validate", "TASK-0001", "TASK-0002"],
        ["task", "validate", "TASK-0001", "--all"],
    ):
        result = subprocess.run(
            ["aidevos", *arguments],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert result.stdout == ""
        assert "usage:" in result.stderr
        assert "Traceback" not in result.stderr


def test_missing_task_file_is_access_error(tmp_path: Path) -> None:
    result = subprocess.run(
        ["aidevos", "task", "validate", "TASK-9999"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: task file not found: .ai/tasks/TASK-9999/task.md\n"


def test_invalid_document_is_deterministic_validation_error(tmp_path: Path) -> None:
    path = tmp_path / ".ai" / "tasks" / "TASK-0003" / "task.md"
    path.parent.mkdir(parents=True)
    path.write_text((FIXTURES / "malformed.md").read_text(encoding="utf-8"), encoding="utf-8")
    command = ["aidevos", "task", "validate", "TASK-0003"]

    first = subprocess.run(command, cwd=tmp_path, check=False, capture_output=True, text=True)
    second = subprocess.run(command, cwd=tmp_path, check=False, capture_output=True, text=True)

    assert first.returncode == 1
    assert first.stdout == ""
    assert first.stderr.startswith("TASK-0003: invalid\nR1:")
    assert "Traceback" not in first.stderr
    assert second.returncode == first.returncode
    assert second.stdout == first.stdout
    assert second.stderr == first.stderr


def test_transition_success_through_console_script(tmp_path: Path) -> None:
    path = write_status(tmp_path)

    result = subprocess.run(
        ["aidevos", "task", "transition", "TASK-0004", "READY_FOR_REVIEW"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout == "TASK-0004: IMPLEMENTING -> READY_FOR_REVIEW\n"
    assert result.stderr == ""
    assert "status: READY_FOR_REVIEW" in path.read_text(encoding="utf-8")
    updated_at = next(
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("updated_at:")
    )
    parsed = datetime.strptime(updated_at, "updated_at: %Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    assert parsed <= datetime.now(timezone.utc)


def test_transition_disallowed_and_classification_errors_through_cli(tmp_path: Path) -> None:
    cases = (
        ("APPROVED", "COMPLETED", 1, "error: disallowed transition: APPROVED -> COMPLETED\n"),
        ("IMPLEMENTING", "WOBBLE", 2, "error: unknown target state: WOBBLE\n"),
        (
            "IMPLEMENTING",
            "BLOCKED",
            2,
            "error: state not supported by TASK-0004: BLOCKED\n",
        ),
    )
    for index, (current, target, code, error) in enumerate(cases):
        root = tmp_path / str(index)
        path = write_status(root, current)
        initial = path.read_bytes()

        result = subprocess.run(
            ["aidevos", "task", "transition", "TASK-0004", target],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == code
        assert result.stdout == ""
        assert result.stderr == error
        assert "Traceback" not in result.stderr
        assert path.read_bytes() == initial


def test_transition_accepts_exactly_two_plain_positionals(tmp_path: Path) -> None:
    for arguments in (
        ["task", "transition"],
        ["task", "transition", "TASK-0004"],
        ["task", "transition", "TASK-0004", "PLANNING", "EXTRA"],
        ["task", "transition", "TASK-0004", "PLANNING", "--all"],
    ):
        result = subprocess.run(
            ["aidevos", *arguments],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert result.stdout == ""
        assert "usage:" in result.stderr
        assert "Traceback" not in result.stderr


def test_transition_malformed_task_id_through_cli(tmp_path: Path) -> None:
    result = subprocess.run(
        ["aidevos", "task", "transition", "foo", "PLANNING"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: invalid Task ID 'foo'; expected TASK-XXXX\n"


def test_transition_console_and_module_entry_points_match_on_independent_copies(
    tmp_path: Path,
) -> None:
    console_root = tmp_path / "console"
    module_root = tmp_path / "module"
    console_path = write_status(console_root)
    module_path = write_status(module_root)
    command = ["task", "transition", "TASK-0004", "READY_FOR_REVIEW"]

    console = subprocess.run(
        ["aidevos", *command],
        cwd=console_root,
        check=False,
        capture_output=True,
        text=True,
    )
    module = subprocess.run(
        ["python", "-m", "aidevos", *command],
        cwd=module_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert module.returncode == console.returncode == 0
    assert module.stdout == console.stdout
    assert module.stderr == console.stderr == ""
    console_lines = console_path.read_text(encoding="utf-8").splitlines()
    module_lines = module_path.read_text(encoding="utf-8").splitlines()
    assert [line for line in module_lines if not line.startswith("updated_at:")] == [
        line for line in console_lines if not line.startswith("updated_at:")
    ]
