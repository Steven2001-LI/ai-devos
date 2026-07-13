from __future__ import annotations

import os
import stat
from datetime import datetime, timedelta, timezone
from itertools import product
from pathlib import Path

import pytest

from aidevos.task_transition import (
    ALLOWED_TRANSITIONS,
    KNOWN_STATES,
    SUPPORTED_STATES,
    transition_task,
)


TASK_ID = "TASK-0004"
FIXED_NOW = datetime(2026, 7, 13, tzinfo=timezone.utc)


def status_document(
    status: str = "IMPLEMENTING",
    *,
    version: str = "3",
    newline: str = "\n",
    final_newline: bool = True,
) -> bytes:
    lines = [
        "# lifecycle state",
        "schema_version: 1",
        f"task_id: {TASK_ID}",
        f"version: {version}",
        f"status: {status}",
        "resume_state: null",
        "blocker:",
        "  status: historical",
        "  updated_by: external_system",
        "branch: feature/task-0004",
        "baseline_commit: 0b7465d",
        "updated_by: human_owner",
        "updated_at: 2026-07-13T07:27:59Z",
    ]
    text = newline.join(lines)
    if final_newline:
        text += newline
    return text.encode()


def write_status(root: Path, content: bytes) -> Path:
    path = root / ".ai" / "tasks" / TASK_ID / "status.yml"
    path.parent.mkdir(parents=True)
    path.write_bytes(content)
    return path


def assert_no_temporary_files(path: Path) -> None:
    assert list(path.parent.glob(".status.yml.*.tmp")) == []


def test_declarative_state_model_is_complete() -> None:
    assert SUPPORTED_STATES == (
        "INBOX",
        "PLANNING",
        "AWAITING_APPROVAL",
        "APPROVED",
        "IMPLEMENTING",
        "READY_FOR_REVIEW",
        "APPROVED_FOR_COMMIT",
        "COMPLETED",
        "REJECTED",
        "CANCELLED",
    )
    assert KNOWN_STATES == (*SUPPORTED_STATES, "BLOCKED")
    assert ALLOWED_TRANSITIONS == {
        "INBOX": frozenset({"PLANNING", "CANCELLED"}),
        "PLANNING": frozenset({"AWAITING_APPROVAL", "CANCELLED"}),
        "AWAITING_APPROVAL": frozenset({"PLANNING", "APPROVED", "REJECTED", "CANCELLED"}),
        "APPROVED": frozenset({"PLANNING", "IMPLEMENTING", "CANCELLED"}),
        "IMPLEMENTING": frozenset({"PLANNING", "READY_FOR_REVIEW", "CANCELLED"}),
        "READY_FOR_REVIEW": frozenset(
            {"PLANNING", "IMPLEMENTING", "APPROVED_FOR_COMMIT", "REJECTED", "CANCELLED"}
        ),
        "APPROVED_FOR_COMMIT": frozenset(
            {"PLANNING", "IMPLEMENTING", "REJECTED", "COMPLETED", "CANCELLED"}
        ),
        "COMPLETED": frozenset(),
        "REJECTED": frozenset(),
        "CANCELLED": frozenset(),
    }


@pytest.mark.parametrize(("current", "target"), tuple(product(SUPPORTED_STATES, repeat=2)))
def test_full_supported_state_matrix(
    current: str,
    target: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial = status_document(current)
    path = write_status(tmp_path, initial)

    result = transition_task(TASK_ID, target, cwd=tmp_path, now=FIXED_NOW)
    output = capsys.readouterr()

    if target in ALLOWED_TRANSITIONS[current]:
        assert result == 0
        assert output.out == f"{TASK_ID}: {current} -> {target}\n"
        assert output.err == ""
        assert path.read_bytes() != initial
    else:
        assert result == 1
        assert output.out == ""
        assert output.err == f"error: disallowed transition: {current} -> {target}\n"
        assert path.read_bytes() == initial
    assert_no_temporary_files(path)


def test_success_updates_exactly_four_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    initial = status_document()
    path = write_status(tmp_path, initial)

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 0

    output = capsys.readouterr()
    assert output.out == f"{TASK_ID}: IMPLEMENTING -> READY_FOR_REVIEW\n"
    assert output.err == ""
    expected = (
        initial.replace(b"version: 3", b"version: 4")
        .replace(b"status: IMPLEMENTING", b"status: READY_FOR_REVIEW")
        .replace(b"updated_by: human_owner", b"updated_by: aidevos_cli")
        .replace(b"updated_at: 2026-07-13T07:27:59Z", b"updated_at: 2026-07-13T00:00:00Z")
    )
    assert path.read_bytes() == expected


def test_arbitrary_length_decimal_version_increments_without_integer_conversion(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    version = "9" * 5_000
    initial = status_document(version=version)
    path = write_status(tmp_path, initial)

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 0

    output = capsys.readouterr()
    assert output.out == f"{TASK_ID}: IMPLEMENTING -> READY_FOR_REVIEW\n"
    assert output.err == ""
    expected = (
        initial.replace(f"version: {version}".encode(), f"version: 1{'0' * 5_000}".encode())
        .replace(b"status: IMPLEMENTING", b"status: READY_FOR_REVIEW")
        .replace(b"updated_by: human_owner", b"updated_by: aidevos_cli")
        .replace(b"updated_at: 2026-07-13T07:27:59Z", b"updated_at: 2026-07-13T00:00:00Z")
    )
    assert path.read_bytes() == expected
    assert_no_temporary_files(path)


@pytest.mark.parametrize(
    ("newline", "final_newline"),
    [("\n", True), ("\n", False), ("\r\n", True), ("\r\n", False)],
)
def test_preserves_comments_order_unrelated_lines_and_newline_style(
    newline: str,
    final_newline: bool,
    tmp_path: Path,
) -> None:
    initial = status_document(newline=newline, final_newline=final_newline)
    path = write_status(tmp_path, initial)

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 0

    updated = path.read_bytes()
    assert updated.startswith(f"# lifecycle state{newline}schema_version: 1".encode())
    assert (
        f"resume_state: null{newline}blocker:{newline}  status: historical{newline}"
        f"  updated_by: external_system{newline}branch: feature/task-0004"
    ).encode() in updated
    assert (updated.endswith(newline.encode())) is final_newline
    if newline == "\r\n":
        assert updated.count(b"\n") == updated.count(b"\r\n")
    else:
        assert b"\r\n" not in updated


def test_preserves_file_permission_mode_bits(tmp_path: Path) -> None:
    path = write_status(tmp_path, status_document())
    path.chmod(0o640)

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 0

    assert stat.S_IMODE(path.stat().st_mode) == 0o640


@pytest.mark.skipif(os.name != "posix", reason="POSIX special mode bits are required")
def test_preserves_special_permission_mode_bits(tmp_path: Path) -> None:
    path = write_status(tmp_path, status_document())
    path.chmod(0o6750)
    if stat.S_IMODE(path.stat().st_mode) != 0o6750:
        pytest.skip("temporary filesystem strips set-user-ID/set-group-ID bits")

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 0

    assert stat.S_IMODE(path.stat().st_mode) == 0o6750
    assert_no_temporary_files(path)


def test_clock_is_converted_to_utc(tmp_path: Path) -> None:
    path = write_status(tmp_path, status_document())
    local_instant = datetime(2026, 7, 13, 10, 30, tzinfo=timezone(timedelta(hours=10)))

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=local_instant) == 0

    assert b"updated_at: 2026-07-13T00:30:00Z" in path.read_bytes()


@pytest.mark.parametrize(
    ("current", "target", "expected_error"),
    [
        ("APPROVED", "COMPLETED", "error: disallowed transition: APPROVED -> COMPLETED\n"),
        ("COMPLETED", "PLANNING", "error: disallowed transition: COMPLETED -> PLANNING\n"),
        ("REJECTED", "INBOX", "error: disallowed transition: REJECTED -> INBOX\n"),
        ("CANCELLED", "APPROVED", "error: disallowed transition: CANCELLED -> APPROVED\n"),
        (
            "IMPLEMENTING",
            "IMPLEMENTING",
            "error: disallowed transition: IMPLEMENTING -> IMPLEMENTING\n",
        ),
    ],
)
def test_disallowed_self_and_terminal_transitions_do_not_write(
    current: str,
    target: str,
    expected_error: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial = status_document(current)
    path = write_status(tmp_path, initial)

    assert transition_task(TASK_ID, target, cwd=tmp_path, now=FIXED_NOW) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == expected_error
    assert path.read_bytes() == initial
    assert_no_temporary_files(path)


@pytest.mark.parametrize(
    ("current", "target", "expected_error"),
    [
        ("IMPLEMENTING", "WOBBLE", "error: unknown target state: WOBBLE\n"),
        (
            "IMPLEMENTING",
            "BLOCKED",
            "error: state not supported by TASK-0004: BLOCKED\n",
        ),
        ("BLOCKED", "PLANNING", "error: state not supported by TASK-0004: BLOCKED\n"),
        (
            "WOBBLE",
            "PLANNING",
            "error: invalid status document: unknown current state: WOBBLE\n",
        ),
    ],
)
def test_state_classification_errors_do_not_write(
    current: str,
    target: str,
    expected_error: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial = status_document(current)
    path = write_status(tmp_path, initial)

    assert transition_task(TASK_ID, target, cwd=tmp_path, now=FIXED_NOW) == 2

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == expected_error
    assert path.read_bytes() == initial
    assert_no_temporary_files(path)


@pytest.mark.parametrize("task_id", ["foo", "TASK-3"])
def test_malformed_task_id_returns_two_without_reading(
    task_id: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected_read(*args: object, **kwargs: object) -> bytes:
        raise AssertionError("read_bytes must not be called")

    monkeypatch.setattr(Path, "read_bytes", unexpected_read)

    assert transition_task(task_id, "PLANNING", now=FIXED_NOW) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"error: invalid Task ID '{task_id}'; expected TASK-XXXX\n"


def test_missing_status_file_returns_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert transition_task("TASK-9999", "PLANNING", cwd=tmp_path, now=FIXED_NOW) == 2

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "error: status file not found: .ai/tasks/TASK-9999/status.yml\n"


def test_directory_instead_of_status_file_returns_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / ".ai" / "tasks" / TASK_ID / "status.yml"
    path.mkdir(parents=True)

    assert transition_task(TASK_ID, "PLANNING", cwd=tmp_path, now=FIXED_NOW) == 2

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"error: status path is not a file: .ai/tasks/{TASK_ID}/status.yml\n"


@pytest.mark.parametrize("error", [PermissionError(), OSError()])
def test_read_failure_returns_two_without_traceback(
    error: OSError,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def failed_read(*args: object, **kwargs: object) -> bytes:
        raise error

    monkeypatch.setattr(Path, "read_bytes", failed_read)

    assert transition_task(TASK_ID, "PLANNING", now=FIXED_NOW) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"error: cannot read status file: .ai/tasks/{TASK_ID}/status.yml\n"
    assert "Traceback" not in output.err


@pytest.mark.parametrize(
    ("mutate", "detail"),
    [
        (
            lambda data: data.replace(b"schema_version: 1\n", b""),
            "missing required key: schema_version",
        ),
        (lambda data: data.replace(b"task_id: TASK-0004\n", b""), "missing required key: task_id"),
        (lambda data: data.replace(b"version: 3\n", b""), "missing required key: version"),
        (lambda data: data.replace(b"status: IMPLEMENTING\n", b""), "missing required key: status"),
        (
            lambda data: data.replace(b"updated_by: human_owner\n", b""),
            "missing required key: updated_by",
        ),
        (
            lambda data: data.replace(b"updated_at: 2026-07-13T07:27:59Z\n", b""),
            "missing required key: updated_at",
        ),
        (
            lambda data: data.replace(
                b"schema_version: 1", b"schema_version: 1\nschema_version: 1"
            ),
            "duplicate required key: schema_version",
        ),
        (
            lambda data: data.replace(
                b"task_id: TASK-0004", b"task_id: TASK-0004\ntask_id: TASK-0004"
            ),
            "duplicate required key: task_id",
        ),
        (
            lambda data: data.replace(b"version: 3", b"version: 3\nversion: 3"),
            "duplicate required key: version",
        ),
        (
            lambda data: data.replace(
                b"status: IMPLEMENTING", b"status: IMPLEMENTING\nstatus: IMPLEMENTING"
            ),
            "duplicate required key: status",
        ),
        (
            lambda data: data.replace(b"updated_by: human_owner", b"updated_by: a\nupdated_by: b"),
            "duplicate required key: updated_by",
        ),
        (
            lambda data: data.replace(
                b"updated_at: 2026-07-13T07:27:59Z",
                b"updated_at: 2026-07-13T00:00:00Z\nupdated_at: 2026-07-13T00:00:01Z",
            ),
            "duplicate required key: updated_at",
        ),
        (
            lambda data: data.replace(b"schema_version: 1", b"schema_version: 2"),
            "unsupported schema_version: 2",
        ),
        (
            lambda data: data.replace(b"version: 3", b"version: -1"),
            "version must be a non-negative integer",
        ),
        (
            lambda data: data.replace(b"version: 3", b"version: 1.5"),
            "version must be a non-negative integer",
        ),
        (
            lambda data: data.replace(b"task_id: TASK-0004", b"task_id: TASK-9999"),
            "task_id TASK-9999 does not match requested Task ID TASK-0004",
        ),
        (
            lambda data: data.replace(b"status: IMPLEMENTING", b'status: "IMPLEMENTING"'),
            "non-canonical required scalar: status",
        ),
        (
            lambda data: data.replace(b"version: 3", b"version:  3"),
            "non-canonical required scalar: version",
        ),
        (
            lambda data: data.replace(b"updated_by: human_owner", b"updated_by : human_owner"),
            "non-canonical required scalar: updated_by",
        ),
    ],
)
def test_invalid_status_documents_do_not_write(
    mutate: object,
    detail: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert callable(mutate)
    initial = mutate(status_document())
    assert isinstance(initial, bytes)
    path = write_status(tmp_path, initial)

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 2

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"error: invalid status document: {detail}\n"
    assert path.read_bytes() == initial
    assert_no_temporary_files(path)


def test_invalid_utf8_is_an_invalid_status_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    initial = status_document() + b"\xff"
    path = write_status(tmp_path, initial)

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 2

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "error: invalid status document: file is not valid UTF-8\n"
    assert path.read_bytes() == initial


def test_success_is_deterministic_across_independent_copies(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_path = write_status(first_root, status_document())
    second_path = write_status(second_root, status_document())

    first_code = transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=first_root, now=FIXED_NOW)
    first_output = capsys.readouterr()
    second_code = transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=second_root, now=FIXED_NOW)
    second_output = capsys.readouterr()

    assert second_code == first_code == 0
    assert second_output == first_output
    assert second_path.read_bytes() == first_path.read_bytes()


def test_failure_is_deterministic_and_leaves_bytes_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    initial = status_document("APPROVED")
    path = write_status(tmp_path, initial)

    first_code = transition_task(TASK_ID, "COMPLETED", cwd=tmp_path, now=FIXED_NOW)
    first_output = capsys.readouterr()
    second_code = transition_task(TASK_ID, "COMPLETED", cwd=tmp_path, now=FIXED_NOW)
    second_output = capsys.readouterr()

    assert second_code == first_code == 1
    assert second_output == first_output
    assert path.read_bytes() == initial


def test_atomic_replace_failure_keeps_original_and_cleans_temp_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial = status_document()
    path = write_status(tmp_path, initial)

    def failed_replace(source: object, destination: object) -> None:
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(os, "replace", failed_replace)

    assert transition_task(TASK_ID, "READY_FOR_REVIEW", cwd=tmp_path, now=FIXED_NOW) == 2

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"error: cannot write status file: .ai/tasks/{TASK_ID}/status.yml\n"
    assert path.read_bytes() == initial
    assert_no_temporary_files(path)
