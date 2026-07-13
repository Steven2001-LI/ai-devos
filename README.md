# AI-DevOS

AI-DevOS is a repository-native pre-commit governance and evidence CLI for AI-generated code.
The CLI includes deterministic validation for repository-native task contracts.

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
aidevos task validate TASK-0001
python -m aidevos --help
python -m aidevos --version
```

Run task validation from the repository root. The command reads
`.ai/tasks/<TASK-ID>/task.md` relative to the current directory and exits `0` for a valid document,
`1` for document validation findings, or `2` for invalid usage and file-access failures.

## Development

```bash
pytest -q
ruff check .
ruff format --check .
mypy src
```
