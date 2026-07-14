"""Parsing and validation for AI-DevOS task documents."""

from __future__ import annotations

import re
import sys
from pathlib import Path


TASK_ID_PATTERN = re.compile(r"TASK-[0-9]{4}")
TITLE_PATTERN = re.compile(r"# (TASK-[0-9]{4}):[ \t]+(\S(?:.*\S)?)\s*")
SECTION_PATTERN = re.compile(r"##\s+(.+?)\s*")
METADATA_PATTERN = re.compile(r"\s*-\s+([^:]+):\s*(.*?)\s*")
ACCEPTANCE_CRITERION_PATTERN = re.compile(r"\s*-\s+\[[ xX]\]\s+AC-[0-9]+:\s+\S.*")
NON_EMPTY_BULLET_PATTERN = re.compile(r"\s*-\s+\S.*")

REQUIRED_SECTIONS = (
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
REQUIRED_METADATA_FIELDS = ("Type", "Priority", "Requested By", "Created")
REQUIRED_LISTS = ("Allowed Patterns", "Restricted Patterns", "Verification Commands")
TYPE_VALUES = ("feature", "bugfix", "refactor", "docs")
PRIORITY_VALUES = ("low", "medium", "high", "critical")


def _parse_sections(text: str) -> dict[str, list[list[str]]]:
    sections: dict[str, list[list[str]]] = {}
    current: list[str] | None = None

    for line in text.splitlines():
        heading = SECTION_PATTERN.fullmatch(line)
        if heading is not None:
            current = []
            sections.setdefault(heading.group(1), []).append(current)
        elif current is not None:
            current.append(line)

    return sections


def _parse_metadata(sections: dict[str, list[list[str]]]) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for occurrence in sections.get("Metadata", []):
        for line in occurrence:
            field = METADATA_PATTERN.fullmatch(line)
            if field is not None:
                fields.setdefault(field.group(1).strip(), []).append(field.group(2))
    return fields


def _section_has_match(
    sections: dict[str, list[list[str]]], section_name: str, pattern: re.Pattern[str]
) -> bool:
    return any(
        pattern.fullmatch(line) is not None
        for occurrence in sections.get(section_name, [])
        for line in occurrence
    )


def extract_section_body(text: str, section_name: str) -> str:
    """Return the first named section body with boundary blank lines removed."""
    occurrences = _parse_sections(text).get(section_name, [])
    if not occurrences:
        return ""

    lines = occurrences[0]
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def extract_non_empty_bullets(text: str, section_name: str) -> list[str]:
    """Return non-empty bullet bodies from the first named section in source order."""
    occurrences = _parse_sections(text).get(section_name, [])
    if not occurrences:
        return []
    return [
        line.strip()[1:].strip()
        for line in occurrences[0]
        if NON_EMPTY_BULLET_PATTERN.fullmatch(line) is not None
    ]


def validate_task_document(task_id: str, text: str) -> list[str]:
    """Return deterministic validation findings for one task document."""
    findings: list[str] = []
    lines = text.splitlines()
    first_non_empty = next((line for line in lines if line.strip()), None)
    title = TITLE_PATTERN.fullmatch(first_non_empty) if first_non_empty is not None else None
    title_task_id = title.group(1) if title is not None else None
    sections = _parse_sections(text)
    metadata = _parse_metadata(sections)

    if title is None:
        findings.append("R1: first non-empty line must match '# TASK-XXXX: <non-empty title>'")

    for section in REQUIRED_SECTIONS:
        count = len(sections.get(section, []))
        if count == 0:
            findings.append(f"R2: missing required section: {section}")
        elif count > 1:
            findings.append(f"R2: duplicate required section: {section}")

    for field in REQUIRED_METADATA_FIELDS:
        values = metadata.get(field, [])
        if not values:
            findings.append(f"R3: missing required Metadata field: {field}")
            continue
        if any(not value for value in values):
            findings.append(f"R3: empty required Metadata field: {field}")
        if len(values) > 1:
            findings.append(f"R3: duplicate required Metadata field: {field}")
            continue
        value = values[0]
        if not value:
            continue
        if field == "Type" and value not in TYPE_VALUES:
            findings.append(
                f"R3: invalid Type '{value}'; expected one of: {', '.join(TYPE_VALUES)}"
            )
        elif field == "Priority" and value not in PRIORITY_VALUES:
            findings.append(
                f"R3: invalid Priority '{value}'; expected one of: {', '.join(PRIORITY_VALUES)}"
            )

    if not _section_has_match(sections, "Acceptance Criteria", ACCEPTANCE_CRITERION_PATTERN):
        findings.append("R4: Acceptance Criteria must contain at least one accepted AC item")

    for section in REQUIRED_LISTS:
        if not _section_has_match(sections, section, NON_EMPTY_BULLET_PATTERN):
            findings.append(f"R5: required list must contain a non-empty bullet: {section}")

    if title_task_id is not None and title_task_id != task_id:
        findings.append(
            f"R6: title Task ID {title_task_id} does not match requested Task ID {task_id}"
        )

    return findings


def validate_task(task_id: str, cwd: Path | None = None) -> int:
    """Read, validate, and report one CWD-relative task document."""
    if TASK_ID_PATTERN.fullmatch(task_id) is None:
        print(f"error: invalid Task ID '{task_id}'; expected TASK-XXXX", file=sys.stderr)
        return 2

    relative_path = Path(".ai") / "tasks" / task_id / "task.md"
    path = (cwd if cwd is not None else Path.cwd()) / relative_path
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: task file not found: {relative_path}", file=sys.stderr)
        return 2
    except IsADirectoryError:
        print(f"error: task path is not a file: {relative_path}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError):
        print(f"error: cannot read task file: {relative_path}", file=sys.stderr)
        return 2

    findings = validate_task_document(task_id, text)
    if findings:
        print(f"{task_id}: invalid", file=sys.stderr)
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1

    print(f"{task_id}: valid")
    return 0
