from __future__ import annotations

import subprocess

import aidevos


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
