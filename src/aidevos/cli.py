"""Command-line interface for AI-DevOS."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from aidevos import __version__
from aidevos.task_transition import transition_task
from aidevos.task_validation import validate_task


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="aidevos",
        description="Repository-native pre-commit governance and evidence CLI for AI-generated code.",
    )
    parser.add_argument("--version", action="version", version=__version__)

    commands = parser.add_subparsers(dest="command", required=True)
    task_parser = commands.add_parser("task", help="Work with task documents.")
    task_commands = task_parser.add_subparsers(dest="task_command", required=True)
    validate_parser = task_commands.add_parser("validate", help="Validate one task document.")
    validate_parser.add_argument("task_id", metavar="TASK-ID")
    transition_parser = task_commands.add_parser(
        "transition", help="Transition one task lifecycle state."
    )
    transition_parser.add_argument("task_id", metavar="TASK-ID")
    transition_parser.add_argument("target_state", metavar="TARGET-STATE")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the AI-DevOS command-line interface."""
    arguments = build_parser().parse_args(argv)
    if arguments.command == "task" and arguments.task_command == "validate":
        return validate_task(arguments.task_id)
    if arguments.command == "task" and arguments.task_command == "transition":
        return transition_task(arguments.task_id, arguments.target_state)
    return 2
