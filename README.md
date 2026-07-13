# AI-DevOS

AI-DevOS is a repository-native governance CLI for AI coding agents. This initial bootstrap exposes
only `--help` and `--version`; protocol gates and task commands are intentionally deferred.

The governing protocol is [AI-DevOS V4.2.1](docs/AI-DevOS-V4.2.1.md).

## Requirements

- Python 3.11 or newer

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Usage

```bash
aidevos --help
aidevos --version
python -m aidevos --help
python -m aidevos --version
```

## Development

```bash
pytest -q
ruff check .
ruff format --check .
mypy src
```
