"""Declarative lifecycle transitions for AI-DevOS task status documents."""

from __future__ import annotations

import os
import re
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from aidevos.task_validation import TASK_ID_PATTERN


SUPPORTED_STATES = (
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
KNOWN_STATES = (*SUPPORTED_STATES, "BLOCKED")
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
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

_REQUIRED_KEYS = (
    "schema_version",
    "task_id",
    "version",
    "status",
    "updated_by",
    "updated_at",
)
_PLAIN_SCALAR_INDICATORS = frozenset("'\"[]{}|>&*!%@`")


def _line_body(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\n", "\r")):
        return line[:-1]
    return line


def _is_canonical_scalar(line: str, key: str) -> bool:
    prefix = f"{key}: "
    if not line.startswith(prefix):
        return False
    value = line[len(prefix) :]
    return bool(
        value
        and value == value.strip()
        and value[0] not in _PLAIN_SCALAR_INDICATORS
        and "#" not in value
    )


def _parse_status_document(task_id: str, text: str) -> tuple[dict[str, str], dict[str, int]]:
    lines = text.splitlines(keepends=True)
    bodies = [_line_body(line) for line in lines]
    values: dict[str, str] = {}
    positions: dict[str, int] = {}

    for key in _REQUIRED_KEYS:
        occurrence_pattern = re.compile(rf"^{re.escape(key)}[ \t]*:")
        occurrences = [
            index for index, line in enumerate(bodies) if occurrence_pattern.match(line) is not None
        ]
        if not occurrences:
            raise ValueError(f"missing required key: {key}")
        if len(occurrences) > 1:
            raise ValueError(f"duplicate required key: {key}")

        index = occurrences[0]
        line = bodies[index]
        if not _is_canonical_scalar(line, key):
            raise ValueError(f"non-canonical required scalar: {key}")
        values[key] = line.removeprefix(f"{key}: ")
        positions[key] = index

    if values["schema_version"] != "1":
        raise ValueError(f"unsupported schema_version: {values['schema_version']}")
    if values["task_id"] != task_id:
        raise ValueError(f"task_id {values['task_id']} does not match requested Task ID {task_id}")
    if re.fullmatch(r"[0-9]+", values["version"]) is None:
        raise ValueError("version must be a non-negative integer")

    return values, positions


def _replace_field(line: str, key: str, value: str) -> str:
    ending = line[len(_line_body(line)) :]
    return f"{key}: {value}{ending}"


def _increment_decimal(value: str) -> str:
    digits = list(value)
    index = len(digits) - 1
    while index >= 0 and digits[index] == "9":
        digits[index] = "0"
        index -= 1
    if index < 0:
        return "1" + "".join(digits)
    digits[index] = chr(ord(digits[index]) + 1)
    return "".join(digits)


def _render_updated_document(
    text: str,
    positions: dict[str, int],
    *,
    target_state: str,
    version: str,
    updated_at: str,
) -> bytes:
    lines = text.splitlines(keepends=True)
    replacements = {
        "status": target_state,
        "version": str(version),
        "updated_by": "aidevos_cli",
        "updated_at": updated_at,
    }
    for key, value in replacements.items():
        index = positions[key]
        lines[index] = _replace_field(lines[index], key, value)
    return "".join(lines).encode("utf-8")


def _atomic_replace(path: Path, content: bytes, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fchmod(temporary_file.fileno(), stat.S_IMODE(mode))
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass


def transition_task(
    task_id: str,
    target_state: str,
    cwd: Path | None = None,
    now: datetime | None = None,
) -> int:
    """Validate and atomically perform one task lifecycle transition."""
    if TASK_ID_PATTERN.fullmatch(task_id) is None:
        print(f"error: invalid Task ID '{task_id}'; expected TASK-XXXX", file=sys.stderr)
        return 2

    relative_path = Path(".ai") / "tasks" / task_id / "status.yml"
    path = (cwd if cwd is not None else Path.cwd()) / relative_path
    try:
        content = path.read_bytes()
        mode = path.stat().st_mode
    except FileNotFoundError:
        print(f"error: status file not found: {relative_path}", file=sys.stderr)
        return 2
    except IsADirectoryError:
        print(f"error: status path is not a file: {relative_path}", file=sys.stderr)
        return 2
    except OSError:
        print(f"error: cannot read status file: {relative_path}", file=sys.stderr)
        return 2

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        print("error: invalid status document: file is not valid UTF-8", file=sys.stderr)
        return 2

    try:
        values, positions = _parse_status_document(task_id, text)
    except ValueError as error:
        print(f"error: invalid status document: {error}", file=sys.stderr)
        return 2

    current_state = values["status"]
    if current_state == "BLOCKED" or target_state == "BLOCKED":
        print("error: state not supported by TASK-0004: BLOCKED", file=sys.stderr)
        return 2
    if target_state not in KNOWN_STATES:
        print(f"error: unknown target state: {target_state}", file=sys.stderr)
        return 2
    if current_state not in KNOWN_STATES:
        print(
            f"error: invalid status document: unknown current state: {current_state}",
            file=sys.stderr,
        )
        return 2
    if target_state not in ALLOWED_TRANSITIONS[current_state]:
        print(f"error: disallowed transition: {current_state} -> {target_state}", file=sys.stderr)
        return 1

    instant = now if now is not None else datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    updated_at = instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated_content = _render_updated_document(
        text,
        positions,
        target_state=target_state,
        version=_increment_decimal(values["version"]),
        updated_at=updated_at,
    )

    try:
        _atomic_replace(path, updated_content, mode)
    except OSError:
        print(f"error: cannot write status file: {relative_path}", file=sys.stderr)
        return 2

    print(f"{task_id}: {current_state} -> {target_state}")
    return 0
