# Claude Guidance

Use [AI-DevOS V4.2.1](docs/AI-DevOS-V4.2.1.md) and the active task's approved contract as the source
of truth.

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

## Role Boundary

Respect the active role and task scope. As Engineer, make only approved implementation changes and
do not alter restricted areas. Never commit or push automatically.
