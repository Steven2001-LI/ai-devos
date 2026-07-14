# TASK-0007: Minimal Adapter Boundary

## Metadata

- Type: feature
- Priority: medium
- Requested By: Human Owner
- Created: 2026-07-14

## Background

TASK-0006 implemented deterministic `aidevos handoff generate`, which materializes a Handoff Contract
v1 (`handoff.json`) and a model-independent Prompt Pack (`prompt-pack.md`) from an existing Task's
`task.md`, `plan.md`, `approval.md`, and an explicit reason-annotated context allowlist. TASK-0005
`plan.md` §9 reserves TASK-0007 as the "minimal Adapter boundary; Contracts stay vendor-decoupled",
between the existing Prompt Pack / Handoff domain and future external coding-agent integrations.

The existing Handoff Contract v1 has no reusable in-memory domain type: it exists only as (a) a
`dict` built inside the private `_build_outputs()` in `src/aidevos/handoff.py` and serialized to
`handoff.json`, and (b) the on-disk `prompt-pack.md` text. `agent_adapter` (`handoff.py`) is a
free-text label, not an interface; no Protocol, ABC, registry, or plugin exists anywhere in the tree.

TASK-0007 defines and validates a boundary only. It introduces one canonical, vendor-neutral,
side-effect-free production transformation that turns an already-produced Handoff Contract v1 mapping
and Prompt Pack text into one deterministic, transport-neutral, deeply immutable Adapter Payload that
future concrete adapters *consume but do not rebuild*. It executes no external agent (no Claude,
Codex, Gemini, Cursor, Aider, or OpenHands), invokes no model, performs no I/O, and adds no
dependency. Payload construction and validation are centralized in AI-DevOS so that future vendor
adapters never each re-implement them. Per the approved Architect review, no Adapter Protocol or ABC
is introduced in TASK-0007; a behavioural adapter interface is deferred to the first concrete-adapter
task, which will establish a real execution interface. Adapter execution, a Workflow Runner, routing,
adapter selection, retry, checkpoint/resume, and Evidence remain owned by future separately approved
adapter tasks and future separately approved workflow/governance tasks. The existing Prompt Pack,
Handoff Contract, Context Manifest, and Context Assembly remain the
single source of truth; TASK-0007 does not duplicate their content model.

## Goal

Add one canonical, vendor-neutral, pure production boundary in a new leaf module
`src/aidevos/adapter.py`: `build_adapter_payload(request) -> AdapterPayload`. It transforms an
already-produced Handoff Contract v1 mapping and Prompt Pack text — held by a thin frozen
`AdapterRequest` (parsed `handoff.json` mapping plus `prompt-pack.md` text) — into a frozen
`AdapterPayload` whose fields are only immutable scalars (`adapter_contract_version: int`,
`instructions: str`, `canonical_handoff_json: bytes`), stamped with `ADAPTER_CONTRACT_VERSION = 1`.
The builder validates the minimum adapter-boundary invariants, normalizes the Prompt Pack text,
canonicalizes and fully detaches the structured input into deterministic canonical JSON bytes, and
returns deterministic output — performing no filesystem, network, subprocess, model, Git, task, or
status operation and importing no vendor SDK and nothing from `handoff.py`/`cli.py`. Its error
vocabulary is exactly `AdapterError` (base), `InvalidAdapterInput`, and `UnsupportedContractVersion`.
Equal valid input always yields an equal payload; the payload is detached so later mutation of the
caller's mapping (top-level or nested) cannot change an already-built payload. `build_adapter_payload`
is the single canonical, supported, validated construction path — the only production function that
performs the full boundary validation, normalization, detachment, and canonicalization; direct
`AdapterPayload` dataclass instantiation is not treated as validated payload construction and no
constructor guard, private token, factory, or metaclass is added to enforce this. Direct production
tests exercise the builder itself (not a test-only fake). No Adapter Protocol/ABC, no concrete vendor
adapter, no CLI change, and no change to `aidevos handoff generate` are introduced.

## Scope

- `src/aidevos/adapter.py` (new leaf module with an explicit standard-library import allowlist of
  `dataclasses`, `collections.abc`, and `json` — `math` may additionally be used only if needed to
  detect non-finite floats; it imports no `os`, `pathlib`, `subprocess`, `socket`, vendor, CLI, Git,
  task, or status dependency, and nothing from `handoff.py`/`cli.py`):
  - `ADAPTER_CONTRACT_VERSION = 1` and a supported input Handoff schema version constant (`1`).
  - `AdapterRequest`: a thin frozen input holder carrying the parsed Handoff Contract v1 mapping and
    the Prompt Pack text. It performs no validation and no I/O and is not described as deeply
    immutable (it may reference the caller's mutable mapping).
  - `AdapterPayload`: a frozen dataclass whose fields are only immutable scalar values —
    `adapter_contract_version: int`, `instructions: str`, `canonical_handoff_json: bytes`. It holds no
    caller-owned mutable container and no execution-result field.
  - `build_adapter_payload(request) -> AdapterPayload`: the single canonical, supported, validated
    construction path. It is the only production function that performs the full boundary validation,
    normalization, detachment, and canonicalization; direct `AdapterPayload` dataclass instantiation
    is not treated as validated payload construction (and no constructor guard, private token,
    factory, or metaclass is added to enforce this). It performs no I/O and mutates neither the request
    nor its mapping.
  - `AdapterError` (base), `InvalidAdapterInput`, `UnsupportedContractVersion` (plain library
    exceptions with stable messages; no exit codes).
- Strict structured-data model and canonical JSON: before serialization the builder recursively
  validates and materializes the structured Handoff Contract input into an ordinary Python
  `dict`/`list` JSON tree, accepting only:
  - object: a `Mapping` with string keys only;
  - array: a `list` only;
  - scalar: `str`, `int`, finite `float`, `bool`, or `None`.
  It rejects, as `InvalidAdapterInput`: a non-string key at any depth; `tuple`; `set`/`frozenset`;
  `bytes`/`bytearray`; any arbitrary custom object; `NaN`, positive Infinity, and negative Infinity; a
  cyclic container; and any value that cannot be represented without implicit Python-to-JSON coercion.
  The validated JSON tree is then serialized with behaviour equivalent to
  `json.dumps(normalized_json_tree, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
  allow_nan=False).encode("utf-8")` — UTF-8 bytes, stable (sorted) key ordering independent of caller
  insertion order, compact separators, Unicode preserved (`ensure_ascii=False`). Recursive
  materialization detaches the payload from all caller-owned mutable state; the builder retains neither
  the original mapping nor any nested mutable object. `json.loads(canonical_handoff_json)` equals the
  validated ordinary JSON tree (and, for valid Handoff Contract v1 input, equals its content). The
  final implementation may express this differently only if behaviour is equivalent and tested; it must
  not build a general serialization framework.
- Version validation on the input Handoff Contract mapping's `schema_version`:
  - missing `schema_version` -> `InvalidAdapterInput`;
  - `schema_version` of the wrong type (for example a string, list, or mapping) -> `InvalidAdapterInput`;
  - a `bool` `schema_version` -> `InvalidAdapterInput` (a `bool` is not accepted as a version integer,
    because `bool` is an `int` subclass in Python — an `isinstance(value, int)` check alone is
    insufficient);
  - a real (non-`bool`) `int` `schema_version` whose value is not `1` -> `UnsupportedContractVersion`;
  - `schema_version == 1` -> valid.
- Prompt Pack normalization of `prompt_pack_text`, in this exact order:
  1. require `prompt_pack_text` to be a `str` (a non-`str` value is `InvalidAdapterInput`);
  2. remove one leading UTF-8 BOM character when present;
  3. normalize CRLF to LF;
  4. normalize standalone CR to LF;
  5. apply `strip()` only to the normalized result to determine whether it is empty or whitespace-only;
  6. if empty after normalization, raise `InvalidAdapterInput`;
  7. return the normalized string without globally stripping it.
  Meaningful leading/trailing whitespace and any final newline are preserved. BOM-only input, and a
  BOM followed only by whitespace/newlines, both normalize to an empty/whitespace-only result and
  therefore raise `InvalidAdapterInput`.
- Determinism and immutability: equal valid `AdapterRequest` input yields an equal `AdapterPayload`
  (value equality on `int`/`str`/`bytes`); `AdapterPayload` is frozen and composed only of deeply
  immutable values, so mutating the caller's mapping after construction cannot alter an existing
  payload.
- `tests/test_adapter.py` (new): direct in-memory production tests of `build_adapter_payload` and the
  value objects, covering the matrix in `plan.md`. A test-only fake is not the sole proof of
  production behaviour. Purity is established by the explicit import allowlist plus a source/code
  review confirming the builder performs only validation, normalization, recursive JSON-tree
  materialization, and JSON serialization — the absence of a filesystem fixture alone does not prove
  purity.
- This task's own governance records under `.ai/tasks/TASK-0007/**`.

## Non-Goals

- No Adapter Protocol or ABC (deferred to the first concrete-adapter task, which will define a real
  execution interface).
- No concrete Claude, Codex, Gemini, Cursor, Aider, OpenHands, or other vendor adapter; no vendor SDK;
  `adapter.py` imports no concrete integration.
- No model invocation, network access, subprocess execution, or any filesystem read or write by the
  builder; reading `handoff.json` / `prompt-pack.md` from disk is a future integration's concern.
- No Git operation and no task or status mutation by the builder.
- No Workflow Runner, routing, adapter selection, registry, or plugin/entry-point discovery.
- No retry or backoff, checkpoint or resume, timeout or cancellation, streaming, concurrency, or
  session management.
- No Evidence generation, automated Review, metrics or tracing, Dashboard, or UI.
- No execution-result fields on the payload (model response, token usage, latency, exit code,
  generated files, tool calls, retry history, checkpoint identifiers, Evidence records) and no
  execution-oriented method (run, execute, invoke, dispatch, route, retry, resume).
- No new CLI command and no change to `aidevos handoff generate` behaviour or output.
- No dependency addition; `[project.dependencies]` stays empty. No package-level re-export of the
  adapter symbols from `src/aidevos/__init__.py` unless separately approved.
- No change to `handoff.py`, `cli.py`, `task_validation.py`, `task_transition.py`, `__init__.py`, or
  `__main__.py`; `adapter.py` is a leaf that nothing in core imports.

## Acceptance Criteria

- [ ] AC-1: `src/aidevos/adapter.py` defines `build_adapter_payload(request) -> AdapterPayload` as the
  single canonical, supported, validated construction path — the only production function that performs
  the full boundary validation, normalization, detachment, and canonicalization. Direct `AdapterPayload`
  dataclass instantiation is not treated as validated payload construction, and no constructor guard,
  private token, factory, or metaclass is added to enforce this.
- [ ] AC-2: No Adapter Protocol and no ABC is defined in `src/aidevos/adapter.py`.
- [ ] AC-3: No vendor or SDK dependency is added; `[project.dependencies]` in `pyproject.toml` remains
  empty; `src/aidevos/adapter.py` imports nothing from any vendor package and nothing from
  `handoff.py` or `cli.py`.
- [ ] AC-4: Every `AdapterPayload` field is one of `int`, `str`, or `bytes` (approximately
  `adapter_contract_version: int`, `instructions: str`, `canonical_handoff_json: bytes`), and the
  instance is frozen.
- [ ] AC-5: Two `build_adapter_payload` calls on equal valid input produce equal `AdapterPayload`
  values, including byte-equal `canonical_handoff_json`.
- [ ] AC-6: Two input mappings with identical content but different key insertion order (top-level and
  nested) produce identical `canonical_handoff_json`.
- [ ] AC-7: `canonical_handoff_json` is UTF-8 bytes with stable (sorted) key ordering, compact
  separators, preserved non-ASCII Unicode, and rejects non-finite floats (`NaN`, positive Infinity,
  negative Infinity) as `InvalidAdapterInput`.
- [ ] AC-8: `canonical_handoff_json` is parseable by strict standard JSON tooling (`json.loads`) back
  to the validated ordinary JSON tree; for valid Handoff Contract v1 input this equals its content.
- [ ] AC-9: The builder validates a strict recursive JSON tree (object = `Mapping` with string keys
  only; array = `list` only; scalar = `str`, `int`, finite `float`, `bool`, or `None`) and rejects, as
  `InvalidAdapterInput`, any non-string key at any depth, `tuple`, `set`/`frozenset`,
  `bytes`/`bytearray`, an arbitrary custom object, a cyclic container, and any value requiring implicit
  Python-to-JSON coercion (no silent key coercion). Focused tests cover at least `tuple` input and
  cyclic input.
- [ ] AC-10: The `AdapterPayload` is detached from all caller-owned mutable containers — it retains no
  reference to the input mapping or any nested mutable object.
- [ ] AC-11: Mutating the original input mapping (top-level or a nested container) after construction
  does not change an already-built `AdapterPayload`.
- [ ] AC-12: `build_adapter_payload` does not mutate its input — the request's mapping and Prompt Pack
  text compare equal to independent pre-call copies afterward.
- [ ] AC-13: A missing or malformed `schema_version` (absent, or a wrong-typed value such as a string,
  list, or mapping) raises `InvalidAdapterInput`.
- [ ] AC-14: A `bool` `schema_version` raises `InvalidAdapterInput` (not `UnsupportedContractVersion`).
- [ ] AC-15: A supported-type real `int` `schema_version` whose value is not `1` raises
  `UnsupportedContractVersion`; `schema_version == 1` is accepted.
- [ ] AC-16: Invalid Prompt Pack input — a non-`str`, an empty string, or a whitespace-only string —
  raises `InvalidAdapterInput`.
- [ ] AC-17: Prompt Pack normalization follows the exact order — require `str`; remove one leading BOM;
  CRLF to LF; standalone CR to LF; apply `strip()` only to the normalized result to test emptiness;
  raise `InvalidAdapterInput` if empty after normalization; otherwise return without globally
  stripping — preserving meaningful leading/trailing whitespace and any final newline. Focused tests
  cover BOM-only input and BOM-followed-only-by-whitespace/newlines, both of which raise
  `InvalidAdapterInput`.
- [ ] AC-18: `build_adapter_payload` performs no filesystem, network, subprocess, model, Git, task, or
  status operation. This is established by the explicit standard-library import allowlist for
  `adapter.py` (no `os`, `pathlib`, `subprocess`, `socket`, vendor, CLI, Git, task, or status
  dependency), direct in-memory behaviour tests, and a source/code review confirming the builder
  performs only validation, normalization, recursive JSON-tree materialization, and JSON serialization
  — absence of a filesystem fixture alone is not treated as proof of purity.
- [ ] AC-19: `AdapterPayload` exposes no execution-result field (model response, token usage, latency,
  exit code, generated files, tool calls, retry history, checkpoint identifier, Evidence) and
  `src/aidevos/adapter.py` exposes no execution-oriented method (run, execute, invoke, dispatch,
  route, retry, resume).
- [ ] AC-20: `pytest -q`, `ruff check .`, `ruff format --check .`, and `mypy src` all pass, and the
  pre-existing test suites continue to pass unchanged in behaviour (baseline 259 passed).

## Allowed Patterns

- `src/aidevos/adapter.py`
- `tests/test_adapter.py`
- `.ai/tasks/TASK-0007/**`

Governance-file ownership: once approved, `task.md` and `plan.md` become read-only and change only via
a bound Amendment; `status.yml` may be changed only through `aidevos task transition` (never
hand-edited). Implementation Agents may write only their assigned implementation paths
(`src/aidevos/adapter.py`, `tests/test_adapter.py`) and specifically authorized report artifacts. The
broad `.ai/tasks/TASK-0007/**` listing above does not authorize an implementation Agent to change the
approved Task Contract (`task.md`) or Plan (`plan.md`).

## Restricted Patterns

- `src/aidevos/handoff.py`, `src/aidevos/cli.py`, `src/aidevos/task_validation.py`,
  `src/aidevos/task_transition.py`, `src/aidevos/__init__.py` (no version bump),
  `src/aidevos/__main__.py` — must not be modified; `adapter.py` must not import from them.
- `tests/test_cli.py`, `tests/test_handoff.py`, `tests/test_task_validation.py`,
  `tests/test_task_transition.py`, `tests/fixtures/**` — existing tests and fixtures, unchanged.
- `pyproject.toml` — no dependency additions (`[project.dependencies]` stays empty), no
  `[project.scripts]` change.
- `README.md`, `docs/**`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`.
- `.ai/tasks/TASK-0001/**`, `.ai/tasks/TASK-0002/**`, `.ai/tasks/TASK-0003/**`,
  `.ai/tasks/TASK-0004/**`, `.ai/tasks/TASK-0005/**`, `.ai/tasks/TASK-0006/**` — historical tasks,
  read only.
- All of `.ai/**` except `.ai/tasks/TASK-0007/**`.
- `.git/**`, `.github/**` — the implementation Agent itself must not create branches or worktrees,
  commit, push, merge, or modify Git metadata, and must make no PR, CI, or history change. This
  restriction binds the implementation Agent only; it does not prohibit the approved orchestration
  workflow: after Human approval, the Management Agent or Human may create `feature/task-0007` and its
  isolated worktree as an orchestration step, and a later approved Release stage may commit or push.

## Verification Commands

- `pytest -q`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `aidevos task validate TASK-0007` (expect: `TASK-0007: valid`, exit 0)
- `aidevos task validate TASK-0004` (expect: `TASK-0004: valid`, exit 0 — no regression)
- `python -m aidevos task validate TASK-0007` (parity check)

## Dependencies

- Baseline commit: `374905f`. TASK-0001 through TASK-0006 are COMPLETED on `main`; no task
  dependencies remain. The planned implementation branch `feature/task-0007` is not created during
  planning or task authoring. TASK-0007 depends only on the already-produced Handoff Contract v1 shape
  (`handoff.json`) and Prompt Pack text (`prompt-pack.md`) and on the Python standard library
  (`dataclasses`, `collections.abc`, `json`); it introduces no runtime dependency.

## Risks

- **Scope creep toward execution / Protocol / vendor integration** — the temptation to add an Adapter
  Protocol/ABC, a concrete vendor adapter, a registry, model invocation, or a run/execute/dispatch
  method. Mitigation: single canonical pure builder; no Protocol/ABC (AC-1/AC-2); explicit Non-Goals
  and deferral to future separately approved adapter and workflow/governance tasks; no
  execution-oriented API (AC-19).
- **Shallow immutability** — a frozen dataclass holding the caller's mutable mapping would let a caller
  mutate the payload's structured content after construction. Mitigation: canonicalize and detach the
  structured input into canonical JSON bytes so the payload retains no caller-owned mutable object
  (AC-10/AC-11); the payload holds only `int`/`str`/`bytes` (AC-4).
- **Non-determinism leaking into canonical JSON** — caller dict ordering, non-finite floats, or key
  coercion would break byte reproducibility or transport neutrality. Mitigation: sorted keys, compact
  separators, `ensure_ascii=False`, `allow_nan=False`, and explicit rejection of non-string keys and
  non-JSON values (AC-6/AC-7/AC-8/AC-9).
- **`bool` schema_version misclassification** — `bool` is an `int` subclass, so `isinstance(v, int)`
  alone would accept `True`/`False` as a version. Mitigation: reject `bool` as `InvalidAdapterInput`
  before the value check (AC-14); classify a missing version as `InvalidAdapterInput` and only a
  present, type-valid, unsupported value as `UnsupportedContractVersion` (AC-13/AC-15).
- **Prompt Pack over-normalization** — globally stripping the instructions would drop meaningful
  leading/trailing whitespace or a final newline and break determinism against the on-disk Prompt
  Pack. Mitigation: strip only for emptiness, normalize BOM and newlines only, preserve the rest
  (AC-16/AC-17).
- **Upward or vendor imports** — importing `handoff.py` (an upward leaf dependency) or a vendor SDK
  would violate the boundary. Mitigation: `adapter.py` imports only stdlib and nothing from core
  modules; newline normalization is re-implemented locally rather than imported (AC-3).
- **Duplicating the content model** — re-declaring the Handoff field set inside the adapter would
  create a second source of truth. Mitigation: carry the validated contract through as canonical
  bytes rather than re-modeling it; the existing Prompt Pack / Handoff domain stays authoritative.
- **Regression to existing behaviour** — any edit outside the two implementation files could disturb
  the 259-test baseline or `aidevos handoff generate`. Mitigation: `adapter.py` is an isolated leaf
  imported by nobody in core; only two implementation files change (AC-20).

## Rollback Notes

- Pre-approval: if rejected or cancelled, advance TASK-0007 only through a legal state transition to
  `REJECTED` or `CANCELLED` via `aidevos task transition`; retain `task.md`, `plan.md`, `status.yml`,
  the decision reason, and audit history. Do not delete the task directory. No implementation exists
  during planning or task authoring.
- Post-implementation: delete `src/aidevos/adapter.py` and `tests/test_adapter.py`. Because
  `adapter.py` is a leaf that nothing in core imports, removing both files restores the baseline with
  no effect on `aidevos handoff generate`, task validation, status transitions, the CLI surface, or
  Git history; no other source, test, `pyproject.toml`, package version, or documentation file is
  changed by an implementation rollback.
- Preserve `.ai/tasks/TASK-0007/**` after approval as governance and audit history. No historical task
  file, `docs/`, `pyproject.toml`, package version, or Git state is changed by a rollback. No
  database, runtime, or deployment rollback is involved.
