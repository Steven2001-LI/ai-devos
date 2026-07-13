# Agent Guidance

Follow [AI-DevOS V4.2.1](docs/AI-DevOS-V4.2.1.md) and the approved files for the active task.

## Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
ruff check .
ruff format --check .
mypy src
```

## Engineer Boundary

Implement only the approved task, stay within its allowed patterns, and do not modify restricted
areas or perform unrelated refactors. Do not automatically commit or push changes.
