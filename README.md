# AI-DevOS

AI-DevOS is a repository-native multi-model software development collaboration and governance system,
built on a pre-commit governance and evidence CLI for AI-generated code.
Implemented today: an installable governance CLI with `task.md` validation, declarative task state
transitions, atomic `status.yml` updates, and deterministic Handoff Contract / Prompt Pack generation
with explicit Context Assembly. Planned (not yet built): replaceable Adapters, a checkpointed
Workflow Runner, and Agent Evaluation.

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
aidevos handoff generate TASK-0001 --handoff-id engineer-to-reviewer --from-role Engineer \
  --to-role Reviewer --agent-adapter local --failure-return-state IMPLEMENTING \
  --context README.md "Project overview"
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
