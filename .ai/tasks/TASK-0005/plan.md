# TASK-0005 Plan

Supports the TASK-0005 Task Contract: a Human-requested governance Meta-task pending ChatGPT
Architect Review and explicit Human Owner Approval. All capabilities below are **future/planned**.

## Planning-Run Guardrails

Constraints on the planning round that authored `task.md`, `plan.md`, `status.yml` — distinct from
the Task Contract's Acceptance Criteria, which govern the post-approval implementation:

- Modifies only `task.md`, `plan.md`, `status.yml`; `status.yml` changes only via legal
  `aidevos task transition` (never hand-edited).
- No Approval created; no `README.md`/`docs/**`/product code changed; no commit/push/branch/worktree.
- The round ends by returning TASK-0005 to `AWAITING_APPROVAL`.

## 1. Repository Baseline

- **Current positioning** (single-tool CLI): `README.md:3`, `pyproject.toml:8`, `cli.py` argparse
  `description`, spec §30.2 — "repository-native pre-commit governance and evidence CLI for
  AI-generated code".
- **Existing foundation**: V4.2.1 already defines a model-agnostic multi-agent governance and
  collaboration foundation — capability-based roles, Task, Approval, Evidence, Review, Git/Worktree,
  model-replaceability (spec §1, §4, §5, line 215). **Implemented**:
  `aidevos task validate`/`transition` (`task_validation.py`, `task_transition.py`); package `0.1.0`.
- **Missing (this direction's target)**: explicit product-level multi-model positioning + an
  executable Handoff Contract, Context Assembly, Adapter, Runner, and Evaluation layer.
- **Defined-but-NOT-implemented** (spec §28 P0/P1): baseline recorder, `scope-check`, candidate
  tree, evidence generator, review/commit gate, event log — no such code; artifacts hand-written.
- **Deferred** (spec §28 + §2.2): automatic Agent scheduling, Dashboard, multi-workflow, Worktree
  CLI, Plugin auto-handoff, Release Workflow, auto Push/Merge, deployment, Token/Cost, auth, sandbox.
- **Baseline**: `main`, clean tree, `HEAD == main == origin/main == 6678bd6`.

## 2. Direction Decision

- **New positioning**: "a repository-native multi-model software development collaboration and
  governance system" — a layer **on top of** the kernel, never bypassing it.
- **Why keep the kernel**: TASK-0001–0004 give validated Task Contracts, a legal state machine, and
  atomic status updates (spec §1.1/§4); collaboration needs these as substrate. **Not claimed
  implemented**: automatic model calls, routing, daemon, dashboard, cloud, auto merge/push/deploy.

## 3. Governance Kernel (preserved)

- **Task Contract** — `task.md` validated by `task_validation.py` (`REQUIRED_SECTIONS`).
- **State Machine** — `task_transition.py` `SUPPORTED_STATES`/`ALLOWED_TRANSITIONS`.
- **Atomic status update** — `task_transition.py:_atomic_replace` (temp + `os.replace` + `fsync`).
- **Approval / Evidence / Review** — `approval.md` (§12), `evidence.md` (§16), `review-NN.md` (§17).
- **Git / Branch / Worktree** — snapshot, diff, isolation, audit boundary (§14, §21); roles are
  capability-based and vendor-neutral (§5, line 215).

## 4. Roles and Adapter Mapping

- **Abstract roles** (capability-based, spec §5): Planner / Coordinator (requirements, approval,
  control), Architect (Repository analysis + design), Engineer (bounded implementation + tests +
  report), Reviewer (independent quality gate), Human Owner (final approval + high-risk ops).
- **Current default Adapter mapping** (replaceable): ChatGPT → Planner/Coordinator; Claude Code →
  Architect; Codex → Engineer; ChatGPT/Claude Code/other → Reviewer; Human Owner → the person.
- **Vendor decoupling**: Task/Handoff/Evidence/Approval Contracts must not depend on vendor names;
  the three products are today's defaults, not required tooling; roles can bind to other models
  (spec line 3 lists Claude Code/Codex/ChatGPT/Gemini/Cursor/Aider/OpenHands).

## 5. Minimum Vertical Slice

Human need → ChatGPT analyzes and writes a Claude Code planning prompt → Claude Code reads the
Repository and produces `task.md`/`plan.md` → ChatGPT reviews → on rejection, structured feedback
returns to Claude Code. On acceptance the **approval chain** runs: ChatGPT produces an Architect
Decision and Approval Draft → Human Owner explicitly confirms → `approval.md` is persisted → the CLI
validates the Task/Plan Hash → status legally advances to `APPROVED`. Then a Codex Prompt Pack is
generated → Codex implements within approved scope, runs verification, produces artifacts → Reviewer
reviews implementation + Evidence → Human Owner controls final Commit/Push/Merge. ChatGPT alone never
forms a formal Repository Approval; gates are explicit Human Owner approval before implementation,
structured failure-return on rejection, and human control of all high-risk operations.

## 6. Future Handoff Contract

Minimal fields (semantics only; Schema/CLI/runtime deferred), each produced by the sending step and
validated downstream:

- `task_id` — owning Task; binds work to scope; stable.
- `handoff_id` — unique per hand-off and the **idempotency key**; a retry needing a new attempt uses
  an explicit derivation rule (e.g. append an attempt counter), never silent reuse.
- `from_role` / `to_role` — sending/receiving abstract roles; receiver validates it is the target.
- `agent_adapter` — concrete Adapter fulfilling `to_role`; vendor-swappable, not part of identity.
- `input_artifacts` — Repository paths the receiver must read; auditable.
- `context_manifest` — pruned context set + reasons (§13.2). **Not a new source of truth**: the
  Repository stays authoritative; downstream verifies the manifest and source digests, not trusting
  the manifest unconditionally.
- `allowed_paths` — receiver write boundary; derived from the Task's Allowed Patterns; enforced.
- `verification_commands` — commands the receiver runs and reports; reproducible.
- `artifact_digest` — digest binding an explicitly enumerated, canonicalized, deterministically
  ordered artifact set; verified downstream for tamper/staleness.
- `status` — hand-off lifecycle state, updated **only by an authorized role or Tooling** per the
  legal Handoff state machine; drives routing.
- `failure_return_state` — a **legal state in the declarative Workflow** to return to on failure.

Future problems (NOT TASK-0005 work): context packing/pruning, structured output, prompt templates,
Human Approval gate, Review-failure return, idempotency, retry/recovery, checkpoint, tamper
detection, Adapter failure handling, resume-after-interrupt, Scope↔Verification↔Evidence linkage;
integrity/stale chain in §13.4.

## 7. Phase-One Operating Model

Human-in-the-loop Prompt Pack: a human manually passes Prompt Packs between models/tools; Repository
structured artifacts carry state and context. No automatic model invocation, daemon, auto-routing,
unattended run, or auto commit/push/merge/deploy. Manual passing is not the end state — it is the
lowest-risk way to validate the Handoff Contract before any automation.

## 8. Minimal Documentation Change Set (future, post-approval)

Exactly two files change; each edit is a single positioning paragraph.

- **`README.md`** — the top product-positioning entry (tagline currently beginning `AI-DevOS is a
  repository-native pre-commit governance and evidence CLI`) plus its one adjacent description line.
  Minimal change: restate the tagline as "AI-DevOS is a repository-native multi-model software
  development collaboration and governance system, built on a pre-commit governance and evidence CLI
  for AI-generated code", preserving the kernel wording. Excluded: Requirements, Install, Usage,
  Development sections and every command/example.
- **`docs/AI-DevOS-V4.2.1.md`** — heading anchor `# AI-DevOS V4.2.1`; current-text anchor: the line
  beginning `> **定位**：一套面向`. Minimal change: extend that single 定位 sentence to name the
  product-level multi-model collaboration-and-governance direction on top of the existing
  model-agnostic protocol. Excluded: the adjacent `> **核心原则**`/`> **当前目标**` lines, `version`,
  document structure, and every other section (Task Schema, state machine, Approval, Scope, Evidence,
  Review, Candidate Snapshot, Commit Gate, roadmap). No new heading or long-form section. Not chosen:
  `AGENTS.md`/`CLAUDE.md`, `pyproject.toml`/`cli.py` (code strings), any new `roadmap.md`.

**Workflow / Governance Artifacts** (not the Implementation Change Set): `task.md`/`plan.md` freeze
after Approval and change only via a bound Amendment; `status.yml` is CLI-owned; `approval.md` is
persisted only on explicit Human Owner confirmation; review/evidence artifacts are created only by
their owning roles — governance artifacts, not Engineer-editable implementation paths.

## 9. Roadmap (TASK-0006 → 0010)

1. **TASK-0006 — Handoff Contract + Prompt Pack Generator** (implementation, not docs). Min: minimal
   validatable Handoff Contract; **Context Manifest v1 + deterministic Context Assembly** (§13.2);
   deterministic Prompt Pack generation from Repository Task/Plan/Approval/context, reusing the CLI.
   Deps: TASK-0005 approved. Non-goals: automatic external model call; no docs-only Context Meta-task.
2. **TASK-0007 — Minimal ChatGPT/Claude Code/Codex Adapter**: minimal Adapter boundary; Contracts
   stay vendor-decoupled. Deps: TASK-0006. Non-goals: complex plugin platform.
3. **TASK-0008 — Checkpointed Workflow Runner**. Min: legal state transitions; Human Gate; checkpoint;
   idempotency; deterministic `failure_return_state`; retry/recovery; resume after interruption;
   append-only audit events. Deps: TASK-0006/0007. Non-goals: distributed scheduling.
4. **TASK-0009 — Scope/Verification/Evidence Integration**. Min: Approval Chain / Task / Plan hash
   binding; Scope enforcement (Allowed Paths); Verification results; test Evidence; artifact/candidate
   digest binding; stale-Evidence and stale-Review detection. Reuses Task/state machine/Review gate.
   Deps: TASK-0008. Non-goals: bypassing human approval.
5. **TASK-0010 — Evaluation Harness** (§13.3). Min: fixed & versioned evaluation task set;
   evaluation-set digest; reproducible run config; prompt/context/model/adapter version recording;
   regression detection; fault injection; single-model baseline; three-model workflow experiment on
   the **same task set, Repository baseline, Acceptance Criteria, and comparable budget**. Deps:
   TASK-0006–0009. Non-goals: dashboard/cloud analytics.

**TASK-0010 planned metrics** — definitions only, dimensioned by `role` and `agent_adapter` (never
fixed vendor roles); model-named rows refer to the Architect/Engineer roles under current defaults:

| Metric | Minimal computation semantic / denominator |
|---|---|
| Handoff Schema valid rate | valid hand-offs ÷ total hand-offs |
| Plan first-approval pass rate (role=Architect, default Claude Code) | plans approved first review ÷ plans submitted |
| Acceptance-criteria completion rate (role=Engineer, default Codex) | ACs met ÷ total ACs |
| Test pass rate | passing tests ÷ total tests executed |
| Scope-violation detection recall | detected true violations ÷ injected violations |
| Scope-violation false-positive rate | FP ÷ (FP + TN) — legitimate (clean) negatives wrongly blocked |
| Injected-failure recovery success rate | recovered runs ÷ injected-failure runs |
| Average human interventions | human gate/manual actions ÷ tasks |
| P50 / P95 end-to-end duration | 50th / 95th pct of `handoff_created` → terminal evaluation outcome; human wait time included and reported separately |
| Average tokens per task | total tokens ÷ tasks, actual Adapter telemetry only |
| Average cost per task | total cost ÷ tasks, actual Adapter telemetry only |
| Single-model vs three-model task-success-rate | success rate(single) vs (three), same task set/baseline/AC/budget |

Integrity: rows are **definitions only**. Token/cost use actual Adapter telemetry only; missing
telemetry = unavailable (never counted as zero); estimates are never presented as measured. TASK-0005
records no observed/current/result/baseline value.

## 10. Risks and Mitigations

Mitigations: 2-file change set (AC-8); capability roles + replaceable Adapters (§4; AC-6);
future/planned framing (AC-4/5); single anchored spec paragraph (§8; AC-2); phase-one
Human-in-the-loop (§7); semantics-only Handoff/Context (§6, §13); definition-only metrics (§9;
AC-12); TASK-0006 as implementation (§9; AC-7).

## 11. Verification Matrix

| AC | Method | Command / evidence | Expected (post-implementation) |
|---|---|---|---|
| AC-1, AC-2, AC-8, AC-10 | grep + git | `grep -Fq "repository-native multi-model software development collaboration and governance system" README.md` ; `git diff -- docs/AI-DevOS-V4.2.1.md` ; `git diff --name-only` | README match; only the §8 paragraph + README entry; no other doc/new file |
| AC-3, AC-9 | git + CLI | `git diff --quiet -- src tests pyproject.toml .ai/tasks/TASK-0001 .ai/tasks/TASK-0002 .ai/tasks/TASK-0003 .ai/tasks/TASK-0004; echo $?` ; `… task validate TASK-0004` | `0` ; `TASK-0004: valid` |
| AC-4..AC-7, AC-11, AC-13 | file review | read `task.md` + `plan.md` §4/§6/§9/§13 | criteria met |
| AC-12 | grep + review | `grep -REn '[0-9]+(\.[0-9]+)?%' .ai/tasks/TASK-0005` (auxiliary) + confirm §9 has only definitions, no observed/current/result/baseline value | none; definitions only |
| AC-14 / structural | review + CLI | read `task.md` ; `PYTHONPATH=src python3 -m aidevos task validate TASK-0005` (zero-install form of `aidevos …`) | placeholder-free ; `TASK-0005: valid` |

## 12. Rollback Notes

- Pre-approval: if rejected or cancelled, advance TASK-0005 only through a legal state transition to
  `REJECTED` or `CANCELLED`; retain `task.md`, `plan.md`, `status.yml`, the decision reason, and
  audit history. Do not delete the task directory.
- Post-implementation: revert only the approved `README.md` and `docs/AI-DevOS-V4.2.1.md` positioning
  changes (isolated `git revert` or restore of prior text). Do not revert or delete TASK-0001–0004,
  the CLI, the Validator, the state machine, or approval history. No database/runtime/deployment
  rollback is involved.

## 13. Four Capability Pillars

Four pillars of **one** product direction (not four Goals) — definition, boundary, owning Task only.

### 13.1 Multi-model Tool/Handoff Orchestration
- **Responsibility**: move bounded work between roles through Repository artifacts using
  capability-based roles, a structured Handoff Contract (§6), a replaceable `agent_adapter`, a Human
  Approval Gate, structured failure return, with Human-in-the-loop as phase one.
- **Boundary**: routes/packages hand-offs on top of Task/Approval/Review/Git; does **not** claim
  automatic scheduling exists, and does not auto-invoke models, auto-merge, or deploy. Owning tasks:
  TASK-0006 (Contract + Prompt Pack), TASK-0007 (Adapter), TASK-0008 (Runner).

### 13.2 Context Engineering
- **Responsibility**: deterministically assemble the context a receiving role needs. The future
  **Context Manifest** must at least express: selected Repository artifacts; selection reasons;
  deterministic relevant-file selection; deduplication; deterministic ordering; token budget;
  over-budget behavior; compression/summarization decisions; provenance from compressed content back to
  source artifacts; Repository revision or file digest; manifest version; canonical manifest digest;
  stale/rebuild behavior.
- **Boundary**: the `context_manifest` is **not** a new source of truth — the Repository remains the
  single source of truth; downstream verifies the manifest digest and source digests rather than
  trusting the manifest unconditionally. No RAG, vector DB, or embedding pipeline.
- **Owning task**: TASK-0006 (Context Manifest v1 + deterministic Context Assembly); no docs-only
  Context Meta-task.

### 13.3 Agent Evaluation
- **Responsibility**: measure hand-off completeness, workflow success, failure recovery, scope
  compliance, and evidence quality with a fixed, versioned, reproducible harness (§9).
- **Boundary**: offline analysis over Repository artifacts and recorded runs; definitions and (later)
  recorded results — never fabricated numbers, no dashboard/cloud platform. Owning task: TASK-0010
  (Evaluation Harness).

### 13.4 Reliability and Engineering Governance
- **Responsibility**: inherit and connect the governance chain end-to-end: Task Hash + Plan Hash →
  Approval Chain Hash → Handoff Contract Digest → Context Manifest Digest → Allowed Paths →
  Verification Results → Evidence / Candidate Digest → Review Decision → Append-only Audit Event. When
  any upstream Contract, Approval Chain, Context, or Artifact changes, every dependent Handoff,
  Evidence, and Review is judged **stale**. Principles only — no Schema or Runtime here.
- **Boundary**: extends the kernel's integrity/stale rules (spec §20); adds no auto-merge,
  auto-deploy, or complex distributed scheduling.
- **Owning tasks**: TASK-0008 (checkpoint/idempotency/audit events), TASK-0009 (hash binding, scope
  enforcement, stale Evidence/Review detection).
