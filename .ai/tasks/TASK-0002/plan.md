# Plan — TASK-0002: Product Positioning Alignment

## Current Implementation Summary

Branch `feature/task-0002` off baseline commit `2fefb85` (TASK-0001 completed and merged). The
working tree was clean before the TASK-0002 governance artifacts were created. Four surfaces
currently carry the pre-confirmation wording:

- `README.md:3` — "AI-DevOS is a repository-native governance CLI for AI coding agents."
- `pyproject.toml:8` — `description = "Repository-native governance for AI coding agents"`.
- `src/aidevos/cli.py:15` — argparse `description="Repository-native governance for AI coding agents."`.
- `docs/AI-DevOS-V4.2.1.md` §30.2 (2869–2871) — "A repository-native governance CLI that coordinates
  AI coding agents through machine-validated task states, scope-aware Git diffs, immutable candidate
  snapshots, reproducible evidence and review-gated commits."

## Technical Baseline (approved)

| Decision | Choice | Reason |
|---|---|---|
| Positioning string | One canonical string across all compact surfaces | Consistency; avoids drift and per-surface variants. |
| Canonical string | "Repository-native pre-commit governance and evidence CLI for AI-generated code." | Confirmed positioning; governs the result (AI-generated code), not the agents. |
| CLI variant | None — no shortened form | Architect directive; single canonical string everywhere. |
| Spec edit | §30.2 one sentence only; `coordinates AI coding agents` → `governs AI-generated code` | Surgical; keeps structure/version/roadmap untouched. |
| Change class | Wording-only | No code logic, no new commands, no dependencies. |
| Version | `0.1.0` unchanged | A wording change does not warrant a version bump. |
| Tests | No new/changed tests | `test_help` asserts only `usage: aidevos`; string change is test-safe. |

## Minimal Implementation Path

Four exact-string replacements, nothing else:

1. `README.md:3` tagline →
   `AI-DevOS is a repository-native pre-commit governance and evidence CLI for AI-generated code.`
   (keep the existing second bootstrap sentence).
2. `pyproject.toml:8` `[project].description` →
   `Repository-native pre-commit governance and evidence CLI for AI-generated code`.
3. `src/aidevos/cli.py:15` argparse `description` →
   `Repository-native pre-commit governance and evidence CLI for AI-generated code.`.
4. `docs/AI-DevOS-V4.2.1.md` §30.2 sentence →
   `A repository-native governance CLI that governs AI-generated code through machine-validated task states, scope-aware Git diffs, immutable candidate snapshots, reproducible evidence and review-gated commits.`

## Expected Change Areas

- `README.md`
- `pyproject.toml`
- `src/aidevos/cli.py`
- `docs/AI-DevOS-V4.2.1.md` (§30.2 sentence only)
- `.ai/tasks/TASK-0002/**` (governance records)

## Test Strategy

No new tests. The change is wording-only and does not alter behavior. The existing suite
(`tests/test_cli.py`) must stay green; `test_help` checks only `"usage: aidevos"`, which is
unaffected. Verification is by exact-string `grep` (AC-1..AC-6), scoped `git diff` on the protocol
doc (AC-7), and the full tooling gate (AC-9): `pytest -q`, `ruff check .`, `ruff format --check .`,
`mypy src`, plus `aidevos --version` / `aidevos --help`. Scope compliance (AC-10) is checked with
both `git status --short --untracked-files=all` (catches tracked and untracked paths) and
`git diff --stat` (tracked-diff summary); together they confirm only Allowed Pattern files are
present or modified.

## Implementation Sequence (Engineer)

1. Edit `README.md:3` tagline to the canonical string; keep the bootstrap sentence.
2. Edit `pyproject.toml:8` `description` to the canonical string.
3. Edit `src/aidevos/cli.py:15` argparse `description` to the canonical string (string only).
4. Edit the single `docs/AI-DevOS-V4.2.1.md` §30.2 sentence (result-governance wording).
5. Run the tooling gate and exact-wording checks; confirm `git diff -- docs/AI-DevOS-V4.2.1.md`
   touches only the §30.2 sentence, and verify scope with both `git status --short
   --untracked-files=all` (every modified or untracked path matches the Allowed Patterns) and
   `git diff --stat` (tracked-diff summary lists only the Allowed Pattern files).
6. Do not commit or push; hand off for review.

## Risk Handling

See `task.md` Risks. Key controls: exact-string acceptance checks prevent wording drift; a scoped
`git diff` on the protocol doc guards against structural/version/roadmap changes; strict Allowed
Patterns keep the diff to four files plus this task's governance records.

## Alternatives Considered

- A shortened CLI-only description variant — rejected by Architect; one canonical string is used on
  every surface.
- Rewriting additional spec sections for full internal consistency — rejected: out of scope; only the
  §30.2 sentence is aligned this task, the rest of the spec already matches the narrow positioning.
- Adding `keywords`/`classifiers`/`[project.urls]` or naming Multica in `README.md` — deferred as
  optional future polish; not required for positioning alignment.
