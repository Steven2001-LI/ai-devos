# Plan — TASK-0007: Minimal Adapter Boundary

## Planning-Run Guardrails

This plan was authored in a planning and task-authoring round. It authorizes no implementation. The
only files written during authoring are the three TASK-0007 governance artifacts (`task.md`,
`plan.md`, and `status.yml`, the last changed only through `aidevos task transition`). No production
code, test, or any other repository file is created or modified; no branch, worktree, commit, push, or
merge occurs. No additional model, subagent, external-agent, API, or Codex invocation occurred — the
current Claude Planner session performed only the approved governance-authoring work. The Acceptance
Criteria in `task.md` govern the later, post-approval implementation.

## 1. Repository Baseline and Currently Implemented Capability

- Baseline commit `374905f`; TASK-0001 through TASK-0006 COMPLETED on `main`; working tree clean; test
  baseline 259 passed.
- Implemented: `aidevos task validate` (`src/aidevos/task_validation.py`), `aidevos task transition`
  with atomic `status.yml` writes (`src/aidevos/task_transition.py`), and `aidevos handoff generate`
  (`src/aidevos/handoff.py`) producing Handoff Contract v1 (`handoff.json`), Context Manifest v1, a
  deterministic Context Assembly, and a Prompt Pack (`prompt-pack.md`).
- Key finding: there is no public in-memory Handoff / Prompt Pack domain type. The contract exists
  only as a private `dict` built in `_build_outputs()` (serialized to `handoff.json`) and as the
  on-disk `prompt-pack.md` text. `_ContextEntry` is private. `agent_adapter` is a free-text label, not
  an interface. No Protocol, ABC, registry, or plugin exists in the tree.
- Existing canonicalization (`handoff.py` `_canonicalize`) is text/newline canonicalization on file
  bytes (UTF-8 decode, one-BOM strip, CRLF/CR to LF). It lives in `handoff.py`, which imports
  `task_transition`/`task_validation`. Importing it into the adapter would be a disallowed upward leaf
  dependency, so the adapter re-implements the same two-line newline normalization locally and adds
  JSON canonicalization via the stdlib `json` module.

## 2. Product and Architecture Decision

Establish the smallest useful vendor-neutral boundary between the existing Prompt Pack / Handoff
domain and future external coding-agent integrations. The approved dependency direction is:

    existing Handoff Contract v1 + Prompt Pack text
        -> one canonical AI-DevOS builder: build_adapter_payload(request)
        -> immutable AdapterPayload
        -> future concrete adapters consume AdapterPayload (they do not rebuild it)

Payload preparation and validation are centralized in AI-DevOS so future vendor adapters never
re-implement them. Per Architect review, no behavioural Adapter Protocol/ABC is introduced now; a real
execution interface is deferred to the first concrete-adapter task. The transformation is deterministic,
local, side-effect-free, and a pure function of its argument.

## 3. Public Contract Shape (pseudocode; not implementation)

    # src/aidevos/adapter.py
    from __future__ import annotations
    from collections.abc import Mapping
    from dataclasses import dataclass

    ADAPTER_CONTRACT_VERSION = 1
    SUPPORTED_HANDOFF_SCHEMA_VERSION = 1

    class AdapterError(Exception): ...
    class InvalidAdapterInput(AdapterError): ...
    class UnsupportedContractVersion(AdapterError): ...

    @dataclass(frozen=True)
    class AdapterRequest:
        handoff_contract: Mapping[str, object]   # parsed handoff.json (source of truth, carried through)
        prompt_pack_text: str                    # prompt-pack.md text

    @dataclass(frozen=True)
    class AdapterPayload:
        adapter_contract_version: int            # == ADAPTER_CONTRACT_VERSION
        instructions: str                        # newline-normalized prompt text
        canonical_handoff_json: bytes            # canonical UTF-8 JSON of the validated contract

    def build_adapter_payload(request: AdapterRequest) -> AdapterPayload: ...

- `build_adapter_payload` is the single canonical, supported, validated construction path: the only
  production function that performs the full boundary validation, normalization, detachment, and
  canonicalization. Direct `AdapterPayload` dataclass instantiation is not treated as validated payload
  construction, and no constructor guard, private token, factory, or metaclass is added to enforce this.
- `AdapterRequest` is a thin, immutable holder. It performs no validation and no I/O and is not
  described as deeply immutable (it may reference the caller's mutable mapping).
- `AdapterPayload` is frozen and composed only of `int`/`str`/`bytes` — deeply immutable, value-
  comparable, transport-neutral, and free of any execution-result field.
- Dependency direction: `adapter.py` imports only `dataclasses`, `collections.abc`, and `json`;
  nothing from `handoff.py`/`cli.py`; no vendor SDK. Nothing in core imports `adapter.py`.

## 4. Strict JSON-Tree Validation, Canonicalization, and Detachment

Before `json.dumps`, the builder recursively validates the structured Handoff Contract input and
materializes it into an ordinary Python `dict`/`list` JSON tree. The accepted recursive model is:

- object: a `Mapping` with string keys only (materialized into a new `dict`);
- array: a `list` only (materialized into a new `list`);
- scalar: `str`, `int` (see the `bool` note below), finite `float`, `bool`, or `None`.

Rejected as `InvalidAdapterInput` (checked during recursive materialization, before serialization):

- a non-string key at any nesting depth (so JSON key coercion of non-string keys never happens
  silently);
- `tuple`;
- `set` / `frozenset`;
- `bytes` / `bytearray`;
- any arbitrary custom object;
- `NaN`, positive Infinity, and negative Infinity;
- a cyclic container (detected during recursion, not by relying on `json.dumps` recursion errors);
- any value that cannot be represented without implicit Python-to-JSON coercion.

The validated ordinary JSON tree is then serialized with behaviour equivalent to:

    json.dumps(
        normalized_json_tree,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

- `sort_keys=True` makes key order independent of the caller's insertion order, recursively (including
  the nested `context_manifest`), giving byte-stable output.
- Recursive materialization is the detachment step: the produced tree and the resulting `bytes` are a
  fresh, deeply immutable snapshot, so mutating the caller's mapping or its nested containers afterward
  cannot alter an already-built payload. The builder retains neither the original mapping nor any nested
  mutable object.
- Round-trip: `json.loads(canonical_handoff_json)` equals the validated ordinary JSON tree; for valid
  Handoff Contract v1 input this also equals its content.
- The Handoff Contract v1 contains only JSON scalars (`str`/`int`), lists, and nested dicts, so
  canonicalization is stable in practice; the `tuple`/`set`/`bytes`/custom-object, non-finite-float,
  non-string-key, and cyclic guards are defensive boundary invariants.
- The final implementation may express this differently only if behaviour is equivalent and tested; it
  must not build a general serialization framework.

## 5. Prompt Pack Normalization

`instructions` are derived from `request.prompt_pack_text` in this exact order:

1. Require `prompt_pack_text` to be a `str`; a non-`str` value is `InvalidAdapterInput`.
2. Remove one leading UTF-8 BOM character when present (mirroring `_canonicalize`, re-implemented
   locally rather than imported).
3. Normalize CRLF to LF.
4. Normalize standalone CR to LF.
5. Apply `strip()` only to the normalized result to determine whether it is empty or whitespace-only.
6. If empty after normalization, raise `InvalidAdapterInput`.
7. Return the normalized string without globally stripping it.

Order matters: the BOM is removed before the emptiness check, because `str.strip()` does not treat
U+FEFF as whitespace. Therefore BOM-only input, and a BOM followed only by whitespace/newlines, both
normalize to an empty/whitespace-only result and raise `InvalidAdapterInput`. Meaningful
leading/trailing whitespace and any final newline are otherwise preserved.

## 6. Validation and Error Semantics

Validated invariants (minimum boundary only; the builder does not re-run task/handoff content
validation, which remains the generator's responsibility):

| Condition | Error |
| --- | --- |
| `handoff_contract` is not a `Mapping` | `InvalidAdapterInput` |
| `schema_version` key absent | `InvalidAdapterInput` |
| `schema_version` present but wrong-typed (str/list/mapping/etc.) | `InvalidAdapterInput` |
| `schema_version` is a `bool` | `InvalidAdapterInput` |
| `schema_version` is a real `int` whose value is not `1` | `UnsupportedContractVersion` |
| `prompt_pack_text` not a `str`, or empty / whitespace-only (after normalization) | `InvalidAdapterInput` |
| non-string mapping key at any depth | `InvalidAdapterInput` |
| `tuple`, `set`/`frozenset`, `bytes`/`bytearray`, or arbitrary custom object at any depth | `InvalidAdapterInput` |
| cyclic container | `InvalidAdapterInput` |
| `NaN` / positive Infinity / negative Infinity | `InvalidAdapterInput` |
| any other value requiring implicit Python-to-JSON coercion | `InvalidAdapterInput` |
| `schema_version == 1`, prompt valid, strict JSON tree (finite scalars only) | success |

Rules: a missing `schema_version` is `InvalidAdapterInput`, never `UnsupportedContractVersion`;
`UnsupportedContractVersion` is reserved for a present, type-valid (real non-`bool` `int`) version
whose value is unsupported. `bool` is rejected explicitly before the value check, because `bool` is an
`int` subclass. All errors are plain library exceptions with stable messages and no exit codes (this
is not a CLI path). No error type exists for network/auth/model/subprocess/timeout/retry.

## 7. Purity and Side Effects

`build_adapter_payload` is a pure function of its argument. It performs no filesystem, network,
subprocess, model, Git, task, or status operation; it does not mutate the request or its mapping.
Reading `handoff.json` / `prompt-pack.md` from disk is the caller's / future integration's concern and
is out of scope here, which also guarantees `aidevos handoff generate` behaviour is untouched.

Purity is established lightweightly by three converging checks, not by the absence of a filesystem
fixture alone:

- an explicit standard-library import allowlist for `adapter.py` — `dataclasses`, `collections.abc`,
  and `json` (and `math` only if needed to detect non-finite floats) — and no `os`, `pathlib`,
  `subprocess`, `socket`, vendor, CLI, Git, task, or status dependency and nothing from
  `handoff.py`/`cli.py`;
- direct in-memory behaviour tests of the builder;
- a source/code review confirming the builder performs only validation, normalization, recursive
  JSON-tree materialization, and JSON serialization.

## 8. Exact Proposed File Change Set

Implementation (post-approval) may create only:

- `src/aidevos/adapter.py` (new leaf module: constants, `AdapterRequest`, `AdapterPayload`,
  `build_adapter_payload`, `AdapterError`, `InvalidAdapterInput`, `UnsupportedContractVersion`).
- `tests/test_adapter.py` (new: direct production tests).

No other file is created or modified. `pyproject.toml` gains no dependency and no script entry.
`src/aidevos/__init__.py` is not changed (no package-level re-export unless separately approved).

## 9. Test Strategy Mapped to Acceptance Criteria

Tests exercise `build_adapter_payload` directly (a test-only fake is never the sole proof).

| Test behaviour | AC |
| --- | --- |
| `build_adapter_payload` is the single validated construction path; direct dataclass instantiation is not validated construction | AC-1 |
| No Protocol/ABC is defined (inspect module symbols / no `Protocol`/`ABC` base) | AC-2 |
| No vendor/SDK import; no import from `handoff.py`/`cli.py`; `[project.dependencies]` empty | AC-3 |
| Payload fields are only `int`/`str`/`bytes`; instance is frozen | AC-4 |
| Equal valid input -> equal payload (byte-equal canonical JSON) | AC-5 |
| Different top-level and nested key insertion order -> identical canonical JSON | AC-6 |
| Canonical JSON is UTF-8, sorted-key, compact, Unicode-preserving; non-finite floats rejected | AC-7 |
| `json.loads(canonical_handoff_json)` equals the validated ordinary JSON tree (and the contract content) | AC-8 |
| Non-string key at any depth -> `InvalidAdapterInput`; focused `tuple` input and cyclic input each -> `InvalidAdapterInput`; `set`/`frozenset`/`bytes`/`bytearray`/custom object rejected | AC-9 |
| Payload holds no reference to the input mapping or nested containers | AC-10 |
| Mutating the original mapping (top-level and nested) after build leaves the payload unchanged | AC-11 |
| Builder does not mutate its input (compare to pre-call copies) | AC-12 |
| Missing / wrong-typed `schema_version` -> `InvalidAdapterInput` | AC-13 |
| `bool` `schema_version` -> `InvalidAdapterInput` | AC-14 |
| Real `int` unsupported version -> `UnsupportedContractVersion`; `1` accepted | AC-15 |
| Non-`str` / empty / whitespace-only prompt -> `InvalidAdapterInput` | AC-16 |
| Exact order (str -> BOM -> CRLF -> CR -> strip-for-emptiness -> return); BOM-only and BOM+whitespace/newlines -> `InvalidAdapterInput`; no global strip; whitespace/final newline preserved | AC-17 |
| Import allowlist enforced + direct in-memory tests + source review confirm no I/O | AC-18 |
| No execution-result field on the payload; no execution-oriented method in the module | AC-19 |
| `pytest -q`, `ruff check .`, `ruff format --check .`, `mypy src` pass; 259 baseline preserved | AC-20 |

## 10. Explicit Deferral Mapping

Deferred work is assigned to categories of future separately approved tasks, not to pre-assigned Task
IDs:

- Adapter Protocol / behavioural execution interface -> the first future separately approved
  concrete-adapter task.
- Concrete Claude/Codex/Gemini/Cursor/Aider/OpenHands adapters, vendor SDKs, model invocation,
  network, subprocess -> future separately approved adapter tasks.
- Workflow Runner, routing, adapter selection, registry, plugin discovery, retry/backoff,
  checkpoint/resume, timeout/cancellation, streaming, concurrency, sessions -> future separately
  approved workflow/governance tasks.
- Scope/Verification/Evidence linkage, automated Review, metrics/tracing, Dashboard/UI -> future
  separately approved workflow/governance tasks.

## 11. Alternatives Rejected and Why They Are Unnecessary for the MVP

- Runtime-checkable Adapter Protocol with a test-only fake as the sole implementation: rejected — a
  Protocol only confirms attribute presence and cannot enforce purity, determinism, validation, or
  immutability; production behaviour must live in a real builder.
- Per-adapter `build_payload`: rejected — payload construction and validation must be centralized so
  future vendor adapters consume, not rebuild, the payload.
- `AdapterPayload` holding a `Mapping` / recursively-frozen structure: rejected in favor of canonical
  JSON bytes — bytes give the deepest immutability, simplest determinism and equality, and no
  re-modeling of the content.
- Re-declaring the Handoff field set as typed payload fields: rejected — it would create a second
  source of truth; the validated contract is carried through as canonical bytes instead.
- Importing `handoff.py` `_canonicalize`: rejected — it is an upward leaf dependency; the two-line
  newline normalization is re-implemented locally.

## 12. Governance Ownership and Git/Worktree Boundary

- Once approved, `task.md` and `plan.md` become read-only and change only via a bound Amendment;
  `status.yml` may be changed only through `aidevos task transition` and is never hand-edited.
- Implementation Agents may write only their assigned implementation paths (`src/aidevos/adapter.py`,
  `tests/test_adapter.py`) and specifically authorized report artifacts; the broad
  `.ai/tasks/TASK-0007/**` listing does not authorize changing the approved Task Contract or Plan.
- The implementation Agent itself must not create branches or worktrees, commit, push, merge, or modify
  Git metadata. This binds the implementation Agent only; it does not prohibit the approved
  orchestration workflow: after Human approval, the Management Agent or Human may create
  `feature/task-0007` and its isolated worktree as an orchestration step, and a later approved Release
  stage may commit or push. The Task Contract does not prohibit that approved management/release
  workflow.

## 13. Rollback Approach

- Pre-approval: advance TASK-0007 only through a legal transition to `REJECTED` or `CANCELLED` via
  `aidevos task transition`; retain the governance artifacts and audit history; do not delete the task
  directory.
- Post-implementation: delete `src/aidevos/adapter.py` and `tests/test_adapter.py`. Because the module
  is an isolated leaf imported by nobody in core, removal restores the baseline with no effect on
  `aidevos handoff generate`, task validation, status transitions, the CLI surface, or Git history.
- Preserve `.ai/tasks/TASK-0007/**` as governance and audit history.
