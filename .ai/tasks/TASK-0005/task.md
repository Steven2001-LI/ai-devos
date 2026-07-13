# TASK-0005: Define Multi-Model Collaboration Product Direction

## Metadata

- Type: docs
- Priority: medium
- Requested By: Human Owner
- Created: 2026-07-13

## Background

This is a Human-requested governance Meta-task pending ChatGPT Architect Review and explicit Human
Owner Approval. The Task Schema (`src/aidevos/task_validation.py`, `TYPE_VALUES`) has no
`meta`/`governance` type, so this task uses the closest legal type `docs` (matching TASK-0002, the
prior positioning task).

V4.2.1 already defines a model-agnostic multi-agent governance and collaboration foundation: the
Protocol already includes capability-based roles, Task, Approval, Evidence, Review, Git/Worktree and
the model-replaceability principle (spec §1, §4, §5). TASK-0001–0004 made part of that kernel
executable (`aidevos task validate`, `aidevos task transition`). What is currently missing is an
explicit product-level multi-model positioning and an executable Handoff Contract, Context Assembly,
Adapter, Runner, and Evaluation layer. Automatic Agent scheduling remains Deferred (spec §28).

This task defines the product direction and its lean roadmap only; it authorizes no runtime code. It
is the Task Contract for a later, minimal documentation implementation. The constraints on the
planning round that authored these files are recorded separately in `plan.md` "Planning-Run
Guardrails"; the Acceptance Criteria below govern that post-approval documentation implementation.

## Goal

Declare the AI-DevOS product direction as "a repository-native multi-model software development
collaboration and governance system" that **preserves** the V4.2.1 governance kernel as its
foundation, defines abstract Roles vs replaceable Adapter mapping, specifies one minimal
human-in-the-loop vertical slice and the minimal future Handoff Contract, and sets a lean
TASK-0006→0010 roadmap — without implementing any runtime code and without claiming unbuilt
automation as done. The direction advances along four capability pillars of one product direction
(not four separate Goals): **Multi-model Tool/Handoff Orchestration**, **Context Engineering**,
**Agent Evaluation**, and **Reliability and Engineering Governance**, all future/planned.

## Scope

- Product positioning: the one-sentence direction above, layered on the existing kernel.
- Four capability pillars of one direction (defined in `plan.md` §13, each with responsibility,
  system boundary, and owning future Task): Multi-model Tool/Handoff Orchestration, Context
  Engineering, Agent Evaluation, Reliability and Engineering Governance. Definition only; no pillar
  is implemented here and none is a separate main Goal.
- Roles (capability-based): Planner / Coordinator, Architect, Engineer, Reviewer, Human Owner —
  and the current **default** Adapter mapping (ChatGPT, Claude Code, Codex) as replaceable, not a
  hard dependency.
- System boundary: what collaboration adds on top of Task / Approval / Evidence / Review / Git,
  never bypassing them.
- First minimal vertical slice: ChatGPT → Claude Code → ChatGPT → Codex → Reviewer → Human Owner,
  with Review, structured failure-return, and human gates (approval chain in `plan.md` §5).
- Phase-one operating model: Human-in-the-loop Prompt Pack (manual hand-off between models;
  Repository-native artifacts carry state).
- Minimal future Handoff Contract field list (see "Handoff Contract Fields"); semantics only.
- Lean roadmap TASK-0006→0010, TASK-0006 = Handoff Contract + Prompt Pack Generator (implementation).
- The minimal documentation Implementation Change Set (see Allowed Patterns / `plan.md` §8). This
  task's own `task.md`/`plan.md`/`status.yml` are governance artifacts, not Engineer-editable
  implementation paths.

## Non-Goals

- No runtime code: no Adapter interface, API client, model call, or vendor SDK.
- No Handoff CLI, Prompt Pack generator, workflow runner, scheduler, or Schema/JSON design.
- No automatic model invocation, daemon, auto-routing, unattended autopilot, or auto
  commit/push/merge/deploy.
- No new large protocol document; no rewrite of `docs/AI-DevOS-V4.2.1.md` structure/version/roadmap.
- Explicitly excluded from this direction and the near-term roadmap: RAG, vector database,
  embedding pipeline, document knowledge-base platform, Dashboard, Web UI, cloud/hosted service,
  distributed scheduling, multi-tenancy, team billing, plugin marketplace, large agent swarm,
  generic workspace manager. (RAG is owned by a separate project and is not re-scoped here.)

## Acceptance Criteria

These criteria verify the post-approval documentation implementation (not the planning round; see
`plan.md` "Planning-Run Guardrails").

- [ ] AC-1: `README.md` top product-positioning entry states the direction "a repository-native
  multi-model software development collaboration and governance system" while keeping the existing
  pre-commit governance/evidence CLI wording (exact target text in `plan.md` §8).
- [ ] AC-2: `docs/AI-DevOS-V4.2.1.md` expresses the multi-model direction only at the single
  paragraph anchored in `plan.md` §8; `version`, document structure, Task Schema, state machine,
  Approval, Scope, Evidence, Review, Candidate Snapshot, and Commit Gate are unchanged.
- [ ] AC-3: The implemented governance kernel and history are unchanged —
  `git diff --quiet -- src tests pyproject.toml .ai/tasks/TASK-0001 .ai/tasks/TASK-0002
  .ai/tasks/TASK-0003 .ai/tasks/TASK-0004` exits 0 and
  `PYTHONPATH=src python3 -m aidevos task validate TASK-0004` prints `TASK-0004: valid`.
- [ ] AC-4: The four capability pillars are documented as future/planned; none is stated as
  implemented.
- [ ] AC-5: No changed document claims that an Adapter, Workflow Runner, automatic scheduling, or
  Evaluation harness already exists.
- [ ] AC-6: Roles and the ChatGPT/Claude Code/Codex Adapter mapping stay vendor-decoupled — the
  Contracts and roles do not hard-depend on any vendor name.
- [ ] AC-7: `plan.md` §9 defines TASK-0006 as Handoff Contract + Prompt Pack Generator (an
  implementation task, not documentation).
- [ ] AC-8: The only changed product-doc locations are the README top positioning entry and the one
  named `docs/AI-DevOS-V4.2.1.md` paragraph — `git diff --name-only` shows no other `README.md` or
  `docs/**` change.
- [ ] AC-9: Product source, tests, configuration, and historical tasks are unchanged (AC-3 command).
- [ ] AC-10: No new long-form protocol document or large new spec section is introduced (no new file
  under `docs/`; the spec edit adds no new heading).
- [ ] AC-11: The Handoff Contract minimal fields are all named (see "Handoff Contract Fields"):
  task_id, handoff_id, from_role, to_role, agent_adapter, input_artifacts, context_manifest,
  allowed_paths, verification_commands, artifact_digest, status, failure_return_state.
- [ ] AC-12: `plan.md` §9 documents all twelve TASK-0010 metrics as definitions only (semantics /
  denominator), dimensioned by `role` and `agent_adapter`, with no observed/current/result/baseline
  value anywhere in TASK-0005.
- [ ] AC-13: The exclusions remain stated: RAG, vector DB, Dashboard, cloud platform, auto-merge,
  auto-deploy, complex distributed scheduling.
- [ ] AC-14: Allowed Patterns, Restricted Patterns, Verification Commands, and Rollback Notes are
  exact and free of placeholders (`<...>`, `TODO`, `TBD`, `path/to`, `TASK-XXXX`).

## Handoff Contract Fields

Minimal semantic fields the future Handoff Contract must express (semantics in `plan.md` §6; not
implemented here): `task_id`, `handoff_id`, `from_role`, `to_role`, `agent_adapter`,
`input_artifacts`, `context_manifest`, `allowed_paths`, `verification_commands`, `artifact_digest`,
`status`, `failure_return_state`.

## Allowed Patterns

Implementation Change Set (Engineer-editable only after Approval):

- `README.md`
- `docs/AI-DevOS-V4.2.1.md`

Task governance artifacts (governance artifacts, **not** Engineer-editable implementation paths;
`status.yml` is CLI-owned; `task.md`/`plan.md` freeze after Approval and change only via a bound
Amendment):

- `.ai/tasks/TASK-0005/task.md`
- `.ai/tasks/TASK-0005/plan.md`
- `.ai/tasks/TASK-0005/status.yml`

## Restricted Patterns

- `.ai/tasks/TASK-0001/**`, `.ai/tasks/TASK-0002/**`, `.ai/tasks/TASK-0003/**`,
  `.ai/tasks/TASK-0004/**` — historical tasks incl. their reviews, approvals, evidence, baselines.
- `src/**` — all product source (`cli.py`, `task_validation.py`, `task_transition.py`,
  `__init__.py`, `__main__.py`); no Adapter/API client, workflow runner, or Handoff CLI is added.
- `tests/**` — all tests and `tests/fixtures/**`.
- `pyproject.toml`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`.
- `.git/**`, `.github/**` — no commit, push, branch, worktree, PR, CI change, or history rewrite.
- `docs/AI-DevOS-V4.2.1.md` `version`, structure, roadmap headings, and every section other than the
  single positioning paragraph anchored in `plan.md` §8 — section-scoped edit only (TASK-0002
  discipline). No new large protocol document, dashboard/web/cloud code, auto merge/push/deploy
  logic, or RAG/vector/embedding implementation may be created.

## Verification Commands

Run by the Engineer to verify the post-approval implementation:

- `grep -Fq "repository-native multi-model software development collaboration and governance system" README.md` (expect: match)
- `git diff -- docs/AI-DevOS-V4.2.1.md` (expect: only the `plan.md` §8 positioning paragraph; no version/structure/schema/state-machine/approval/scope/evidence/review/commit-gate change)
- `git diff --name-only` (expect: only `README.md`, `docs/AI-DevOS-V4.2.1.md`, and the TASK-0005 governance files)
- `git diff --quiet -- src tests pyproject.toml .ai/tasks/TASK-0001 .ai/tasks/TASK-0002 .ai/tasks/TASK-0003 .ai/tasks/TASK-0004` (expect: exit 0)
- `PYTHONPATH=src python3 -m aidevos task validate TASK-0004` (expect: `TASK-0004: valid`, exit 0)
- `PYTHONPATH=src python3 -m aidevos task validate TASK-0005` (expect: `TASK-0005: valid`, exit 0)
- `git diff --check` (expect: no whitespace errors)

## Dependencies

- Baseline commit: `6678bd6`. TASK-0001, TASK-0002, TASK-0003, TASK-0004 are COMPLETED on `main`;
  no task dependencies remain. Planned future implementation branch `feature/task-0005` is not
  created during planning. Uses only the existing CLI and standard library; no runtime dependency.

## Risks

- **Positioning re-bloat / docs over-claiming** — one-sentence direction, 2-file change set, and
  future/planned framing (AC-4/AC-5/AC-8).
- **Vendor-locking roles** — capability-based roles + replaceable Adapter mapping (AC-6).
- **Editing frozen spec structure** — single anchored paragraph in `plan.md` §8 (AC-2).
- **Premature auto-scheduling / Handoff over-design** — phase-one Human-in-the-loop; semantics-only
  fields, Schema/CLI deferred.
- **Fabricated eval numbers** — definition-only metrics (AC-12).
- **TASK-0006 regressing to a doc task** — AC-7 requires it be implementation.

## Rollback Notes

- Pre-approval: if rejected or cancelled, advance TASK-0005 only through a legal state transition to
  `REJECTED` or `CANCELLED`; retain `task.md`, `plan.md`, `status.yml`, the decision reason, and
  audit history. Do not delete the task directory.
- Post-implementation: revert only the approved `README.md` positioning change and the approved
  `docs/AI-DevOS-V4.2.1.md` positioning change (isolated `git revert` or restore of prior text). Do
  not revert or delete TASK-0001–0004, the CLI, the Validator, the state machine, or approval
  history. No database, runtime, or deployment rollback is involved.
