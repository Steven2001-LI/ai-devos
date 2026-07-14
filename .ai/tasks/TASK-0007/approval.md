# Task Approval

- Task: TASK-0007
- Decision: APPROVED
- Reviewed Task Hash: sha256:1a9fa2e2dc470cacd9c41d63b892cbe5f862f4bb3e60aa03afbe6a2a75bd8a81
- Reviewed Plan Hash: sha256:feda22252ff58ff73ea4bf19f4a8cd2b632f8253c1b1eee98074d44dccaec9a0
- Approved By: Human Owner
- Generated With: GPT-5.6 Thinking Architect Review
- Approved At: 2026-07-14T13:57:37Z

## Scope Assessment

PASS.

TASK-0007 is approved only for the minimal vendor-neutral Adapter Payload boundary defined in the
current `task.md` and `plan.md`. Production implementation is limited to exactly two files:
`src/aidevos/adapter.py` and `tests/test_adapter.py`.

The approved boundary introduces one canonical, pure builder `build_adapter_payload(request) ->
AdapterPayload` — the single canonical, supported, validated construction path — with a thin frozen
`AdapterRequest` input holder, a deeply immutable `AdapterPayload` (`adapter_contract_version: int`,
`instructions: str`, `canonical_handoff_json: bytes`), the `ADAPTER_CONTRACT_VERSION = 1` constant,
and the `AdapterError` / `InvalidAdapterInput` / `UnsupportedContractVersion` error family.

Out of scope and not authorized: any Adapter Protocol or ABC; any concrete vendor adapter (Claude,
Codex, Gemini, Cursor, Aider, OpenHands, or other); any vendor SDK; any model invocation, network
access, subprocess execution, filesystem read or write, Git operation, or task/status mutation by the
builder; a Workflow Runner, routing, adapter selection, registry, plugin discovery, retry or backoff,
checkpoint or resume, timeout or cancellation, streaming, concurrency, or session management; Evidence
generation, automated Review, metrics or tracing, Dashboard or UI; any new CLI command or change to
`aidevos handoff generate`; any dependency addition; and any package-level re-export of the adapter
symbols from `src/aidevos/__init__.py`.

## Architecture Assessment

PASS.

The approved design is a deterministic standard-library transformation. `build_adapter_payload` is the
only production function that performs the full boundary validation, normalization, detachment, and
canonicalization; direct `AdapterPayload` dataclass instantiation is not treated as validated payload
construction, and no constructor guard, private token, factory, or metaclass is introduced.

Binding architectural requirements from the approved Task and Plan: `adapter.py` is a leaf module with
an explicit standard-library import allowlist (`dataclasses`, `collections.abc`, `json`; `math` only
if needed to detect non-finite floats) that imports nothing from `handoff.py`/`cli.py` and no vendor
SDK, and that nothing in core imports. The builder validates a strict recursive JSON tree (object =
`Mapping` with string keys only; array = `list` only; scalar = `str`, `int`, finite `float`, `bool`,
or `None`), recursively materializes and detaches it into ordinary Python `dict`/`list` data, and
serializes to canonical bytes equivalent to `json.dumps(normalized_json_tree, ensure_ascii=False,
sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")`. It rejects, as
`InvalidAdapterInput`, non-string keys at any depth, `tuple`, `set`/`frozenset`, `bytes`/`bytearray`,
arbitrary custom objects, `NaN` and positive/negative Infinity, cyclic containers, and any value
requiring implicit Python-to-JSON coercion. Version handling: a missing or wrong-typed `schema_version`
and a `bool` `schema_version` raise `InvalidAdapterInput`; only a real `int` whose value is unsupported
raises `UnsupportedContractVersion`; `1` is valid. Prompt normalization follows the exact order — require
`str`, remove one leading BOM, CRLF to LF, standalone CR to LF, `strip()` only to test emptiness, raise
`InvalidAdapterInput` if empty, otherwise return without global stripping — preserving meaningful
whitespace and any final newline. The payload is deeply immutable and detached, so mutating the caller's
mapping (top-level or nested) after construction cannot alter it.

## Acceptance Criteria Assessment

PASS.

The current Task and Plan define twenty externally verifiable Acceptance Criteria with observable
coverage for: the single canonical builder; absence of any Protocol/ABC; absence of vendor/SDK
dependency and upward imports; the `int`/`str`/`bytes`-only frozen payload; equal-input determinism;
order-independent canonical JSON; UTF-8, sorted-key, compact, Unicode-preserving serialization with
non-finite-float rejection; strict-JSON round-trip to the validated JSON tree; strict-tree rejection of
non-string keys, `tuple`, `set`/`frozenset`, `bytes`/`bytearray`, custom objects, and cyclic containers;
payload detachment and post-mutation stability; input non-mutation; the full version-validation matrix
including the `bool` distinction; prompt normalization including BOM-only and BOM+whitespace rejection;
purity established by import allowlist plus in-memory tests plus source review; the absence of any
execution-result field or execution-oriented method; and the passing verification suite with the 259-test
baseline preserved.

## Conditions

None beyond the approved task.md and plan.md.

`task.md` and `plan.md` freeze immediately after this Approval and change only through a formally
approved Amendment that binds the applicable hashes. This Approval is valid only for the exact Task and
Plan SHA-256 values recorded above.
