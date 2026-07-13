from __future__ import annotations

import subprocess
from pathlib import Path

import aidevos


FIXTURES = Path(__file__).parent / "fixtures" / "tasks"


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
