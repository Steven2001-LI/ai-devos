# TASK-0002: Product Positioning Alignment

## Metadata

- Type: docs
- Priority: medium
- Requested By: Human Owner
- Created: 2026-07-13

## Background

TASK-0001 established the installable `aidevos` CLI skeleton. The confirmed product positioning
for AI-DevOS is the single canonical string:

> Repository-native pre-commit governance and evidence CLI for AI-generated code.

with the Multica relationship: Multica dispatches the work; AI-DevOS governs the result.

The repository's compact self-descriptions predate this confirmation and read "a repository-native
governance CLI **for AI coding agents**" — missing the **pre-commit** and **evidence** framing and
centering **agents** rather than the **AI-generated code (the result)**. In addition, the protocol
doc's §30.2 one-sentence blurb says AI-DevOS "**coordinates AI coding agents**," which reads as
orchestration rather than result governance. This task aligns those surfaces with the canonical
string. It is a wording-only product-positioning alignment; no roadmap capability is implemented.

Note: the original scoping brief referenced `.ai/project/` files. No `.ai/project/` directory
exists; the authoritative positioning lives in `docs/AI-DevOS-V4.2.1.md` and `README.md`.

## Goal

Make every compact product-facing self-description of AI-DevOS — README tagline, package metadata,
CLI `--help`, and the spec §30.2 one-sentence blurb — express the confirmed positioning:
**repository-native pre-commit governance and evidence CLI for AI-generated code** that governs the
result. Remove "for AI coding agents" from the aligned compact surfaces and "coordinates AI coding
agents" from §30.2. No behavioral or roadmap-capability change.

## Scope

Wording-only edits, one canonical string, exact final forms:

- `README.md:3` — tagline sentence becomes exactly:
  `AI-DevOS is a repository-native pre-commit governance and evidence CLI for AI-generated code.`
  Keep the existing second sentence about the bootstrap (`--help`/`--version` only, gates deferred).
- `pyproject.toml:8` — `[project].description` value becomes exactly:
  `Repository-native pre-commit governance and evidence CLI for AI-generated code`
- `src/aidevos/cli.py:15` — argparse `description` string only (no logic change), becomes exactly:
  `Repository-native pre-commit governance and evidence CLI for AI-generated code.`
  No shortened CLI variant.
- `docs/AI-DevOS-V4.2.1.md` §30.2 (lines 2869–2871) — change **only** the one sentence, replacing
  the orchestration phrase `coordinates AI coding agents` with result-governance wording. Final
  sentence:
  `A repository-native governance CLI that governs AI-generated code through machine-validated task states, scope-aware Git diffs, immutable candidate snapshots, reproducible evidence and review-gated commits.`
  No change to document structure, version, roadmap, headings, or any other section/sentence.

Plus this task's own governance records under `.ai/tasks/TASK-0002/**`.

## Non-Goals

All later-roadmap capabilities remain explicitly out of scope:

- Task/schema **validation** implementation (roadmap #2).
- Declarative **state-transition** implementation (roadmap #3).
- Scope-aware **Git diff enforcement** (roadmap #4).
- **Immutable candidate snapshots** (roadmap #5).
- **Evidence generation** implementation (roadmap #6) — "evidence" is added as positioning wording
  only; no evidence feature is built.
- **Review / commit-gate** implementation (roadmap #7).
- Any **dashboard, UI**, daemon, cloud runtime, agent routing/scheduling, automatic push, or
  automatic merge.
- Any edit to `docs/AI-DevOS-V4.2.1.md` **other than** the single §30.2 sentence — no change to its
  structure, `version`, roadmap, or any other section.
- Adding `keywords` / `classifiers` / `[project.urls]` to `pyproject.toml`.
- Naming Multica in `README.md`.
- Version bump of `src/aidevos/__init__.py` (`0.1.0` stays).
- Unrelated refactoring; dependency additions/upgrades.

## Acceptance Criteria

- [ ] AC-1: `README.md` line 3 is exactly
  `AI-DevOS is a repository-native pre-commit governance and evidence CLI for AI-generated code.`
- [ ] AC-2: `pyproject.toml` `[project].description` is exactly
  `Repository-native pre-commit governance and evidence CLI for AI-generated code`
- [ ] AC-3: `src/aidevos/cli.py` argparse `description` is exactly
  `Repository-native pre-commit governance and evidence CLI for AI-generated code.`
  and `aidevos --help` prints that exact sentence.
- [ ] AC-4: `docs/AI-DevOS-V4.2.1.md` §30.2 blurb is exactly
  `A repository-native governance CLI that governs AI-generated code through machine-validated task states, scope-aware Git diffs, immutable candidate snapshots, reproducible evidence and review-gated commits.`
- [ ] AC-5: The phrase `for AI coding agents` does not appear in `README.md`, `pyproject.toml`, or
  `src/aidevos/cli.py`.
- [ ] AC-6: The phrase `coordinates AI coding agents` does not appear in the §30.2 summary (nor
  elsewhere in `docs/AI-DevOS-V4.2.1.md`).
- [ ] AC-7: In `docs/AI-DevOS-V4.2.1.md`, the diff touches only the §30.2 sentence — no change to
  structure, `version`, roadmap, or any other section (verified via `git diff`).
- [ ] AC-8: No new capability claim (orchestration, dashboard, daemon, auto-merge/push, "operating
  system") is introduced in any changed file; every diff is wording-only (no code logic, no new
  commands).
- [ ] AC-9: `pytest -q`, `ruff check .`, `ruff format --check .`, `mypy src` all pass;
  `aidevos --version` prints `0.1.0` and exits 0; `aidevos --help` exits 0.
- [ ] AC-10: No tracked or untracked files outside the Allowed Patterns exist. Verified using both
  `git status --short --untracked-files=all` (every modified or untracked path matches the Allowed
  Patterns) and `git diff --stat` (tracked-diff summary lists only Allowed Pattern files).

## Allowed Patterns

Approved implementation files (exact, no broad wildcards):

- `README.md`
- `pyproject.toml`
- `src/aidevos/cli.py` (argparse `description` string only)
- `docs/AI-DevOS-V4.2.1.md` (§30.2 one sentence only)

Governance records for this task:

- `.ai/tasks/TASK-0002/**`

## Restricted Patterns

- `docs/AI-DevOS-V4.2.1.md` beyond the single §30.2 sentence — no change to structure, `version`,
  roadmap, headings, or any other section.
- `src/aidevos/__init__.py` (no version bump), `src/aidevos/__main__.py`.
- `src/aidevos/cli.py` beyond the single argparse `description` string (no parser/logic changes).
- `tests/**` — behavior unchanged; no test edits.
- `.ai/tasks/TASK-0001/**`, `.gitignore`, `CLAUDE.md`, `AGENTS.md`.
- `.git/**`.
- All of `.ai/**` except `.ai/tasks/TASK-0002/**`.
- No new CLI commands, modules, dependencies, or files beyond the Allowed Patterns.

## Verification Commands

- `pytest -q`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `aidevos --version` (expect: `0.1.0`, exit 0)
- `aidevos --help` (expect: exact aligned description, exit 0)
- `python -m aidevos --help` (parity check)
- `grep -Fq "AI-DevOS is a repository-native pre-commit governance and evidence CLI for AI-generated code." README.md`
- `grep -Fq "Repository-native pre-commit governance and evidence CLI for AI-generated code" pyproject.toml`
- `grep -Fq "Repository-native pre-commit governance and evidence CLI for AI-generated code." src/aidevos/cli.py`
- `grep -Fq "governs AI-generated code through" docs/AI-DevOS-V4.2.1.md`
- `grep -R "for AI coding agents" README.md pyproject.toml src/aidevos/cli.py` (expect: no matches)
- `grep -F "coordinates AI coding agents" docs/AI-DevOS-V4.2.1.md` (expect: no matches)
- `git diff -- docs/AI-DevOS-V4.2.1.md` (expect: only the §30.2 sentence changed)
- `git status --short --untracked-files=all` (expect: every modified or untracked path matches the
  Allowed Patterns)
- `git diff --stat` (tracked-diff summary; expect: only the Allowed Pattern files — does not by
  itself detect untracked files, pair it with `git status --short --untracked-files=all`)

## Dependencies

- Baseline commit: `2fefb85`. Branch: `feature/task-0002`. TASK-0001 is completed and merged into
  `main`. No task dependencies remain.

## Risks

- **Spec §30.2 edit precision** — this is the only permitted change inside the 3158-line authoritative
  spec. The Engineer must edit exactly that one sentence and nothing else; AC-7 and the scoped
  `git diff` guard against accidental structural/version/roadmap drift.
- **Exact-wording drift** — the four surfaces must match the canonical string byte-for-byte;
  AC-1..AC-4 use exact-string checks rather than token presence.
- **Test safety** — `tests/test_cli.py::test_help` asserts only `"usage: aidevos"`, not the
  description, so the CLI string change is test-safe; no test edits are required.
- **Process hygiene** — TASK-0001 review-02 flagged a baseline mismatch (N-004). TASK-0002 cites one
  baseline consistently: `2fefb85`.

## Commit Policy

No commit or push during planning or implementation. Commit is allowed only after final approval and
through the designated release step.

## Rollback Notes

All changes are minimal text reversions. Rollback = restore the original tagline in `README.md:3`,
the original `description` in `pyproject.toml:8` and `src/aidevos/cli.py:15`, and the original §30.2
sentence in `docs/AI-DevOS-V4.2.1.md`, then delete `.ai/tasks/TASK-0002/`. No structural or code-logic
change is made.
