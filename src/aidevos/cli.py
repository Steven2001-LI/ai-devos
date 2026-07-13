"""Command-line interface for AI-DevOS."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from aidevos import __version__


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="aidevos",
        description="Repository-native pre-commit governance and evidence CLI for AI-generated code.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the AI-DevOS command-line interface."""
    build_parser().parse_args(argv)
    return 0
