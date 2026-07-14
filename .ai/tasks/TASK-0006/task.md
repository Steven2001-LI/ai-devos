# TASK-0006: Handoff Contract + Prompt Pack Generator

## Metadata

- Type: feature
- Priority: high
- Requested By: Human Owner
- Created: 2026-07-13

## Background

TASK-0001 built the installable `aidevos` CLI skeleton, TASK-0003 added deterministic
`aidevos task validate` for the AI-DevOS V4.2.1 §8 `task.md` contract, and TASK-0004 added
`aidevos task transition` with an atomic `status.yml` writer. TASK-0005 declared the product
direction — "a repository-native multi-model software development collaboration and governance
system" — and named TASK-0006 as the next *implementation* task: **Handoff Contract + Prompt Pack
Generator, including Context Manifest v1 and deterministic Context Assembly** (TASK-0005 `plan.md`
§9, approved in `.ai/tasks/TASK-0005/approval.md`).

The Repository is the single source of truth (spec §4). Today, moving bounded work between roles is
purely manual: nothing renders an existing Task into a model-independent, byte-deterministic package
that a Human can hand to the next Agent, and nothing binds that package to the exact bytes of the
Repository artifacts it carries. TASK-0006 adds one command that deterministically materializes a
Handoff Contract v1 (`handoff.json`) and a model-independent Prompt Pack (`prompt-pack.md`) from an
existing Task's `task.md`, `plan.md`, `approval.md`, and an explicit, reason-annotated allowlist of
additional context files. A Human still manually passes the generated Prompt Pack to the next Agent
(TASK-0005 §7, phase-one Human-in-the-loop); no model is invoked.

`approval.md` is a **required primary input artifact**: the generator verifies only its safe presence
and canonical bytes. TASK-0006 does **not** validate the Approval's Decision, Task Hash, Plan Hash,
approver authority, or Approval Chain, and the generated Prompt Pack does not assert that Approval
validity has been established; full Approval / Contract binding remains deferred to TASK-0009. The
command reuses the existing CLI and the Python standard library only; it introduces no runtime
dependency, no vendor SDK, no network access, and no new source of truth. `agent_adapter` is a
descriptive label, never an import. A Handoff lifecycle state machine, Scope enforcement, verification
execution, Evidence, and Adapter code are out of scope and owned by later tasks (see Non-Goals and
`plan.md` §14).

## Goal

Add a deterministic `aidevos handoff generate <TASK-ID>` command that safely reads an existing
Repository Task's required primary artifacts (`.ai/tasks/<TASK-ID>/task.md`, `plan.md`,
`approval.md`), **validates `task.md` with the existing structural rules R1–R6 before extracting
anything from it**, assembles a caller-supplied, explicitly reason-annotated allowlist of additional
Repository context files, and writes exactly two files under a deterministic, containment-checked,
never-overwritten output directory `.ai/tasks/<TASK-ID>/handoffs/<HANDOFF-ID>/` — a machine-readable
Handoff Contract v1 (`handoff.json`) and a fixed, model-independent Prompt Pack (`prompt-pack.md`) —
such that identical Repository contents and identical semantic arguments always produce byte-for-byte
identical output, with stable scriptable exit codes (0 generated, 1 readable-and-path-safe inputs
form an invalid Handoff/Task contract, 2 invalid invocation / unsafe path / inaccessible file /
decoding error / output collision / I/O error). The command may create the task-local
`.ai/tasks/<TASK-ID>/handoffs/` output area when absent and one final `<HANDOFF-ID>/` directory
beneath it. It performs no mutation outside that task-local output area and does not modify
`task.md`, `plan.md`, `approval.md`, `status.yml`, lifecycle state, Git index, branch, history, or
external systems. The implementation
lands in one new module `src/aidevos/handoff.py`, minimal CLI wiring in `src/aidevos/cli.py`, and an
additive deterministic section/list extractor exposed from `src/aidevos/task_validation.py`; no new
runtime dependency.

## Scope

- `src/aidevos/handoff.py` (new): `generate_handoff(task_id, handoff_id, from_role, to_role,
  agent_adapter, failure_return_state, context_specs, cwd=None) -> int`, where `context_specs` is an
  ordered list of `(path, reason)` pairs. Performs, fail-fast (evaluation order fixed in `plan.md`
  §10): argument/ID/`handoff_id` format and text-scalar checks → `failure_return_state` membership →
  safe read + UTF-8 decode + `validate_task_document` of `task.md` → read/decode of `plan.md` and
  `approval.md` → additional context safety, decoding, and manifest assembly → deterministic
  Contract/Prompt Pack byte construction → output-containment check → single-process publish that
  refuses a pre-existing destination. No network, no vendor import.
- `src/aidevos/cli.py`: add a `handoff` command group with a `generate` subcommand. Argparse
  validates structure/arity only. Accepts one positional `TASK-ID` and options `--handoff-id`,
  `--from-role`, `--to-role`, `--agent-adapter`, `--failure-return-state`, and repeatable
  `--context PATH REASON` (`nargs=2`, `action="append"`). Preserve existing `--help`/`--version`/
  `task validate`/`task transition`. Exact flag names are fixed in `plan.md` §4.
- `src/aidevos/task_validation.py`: additively expose deterministic Task section/list extraction
  (a section-body reader and a non-empty-bullet list reader) reusing the existing `_parse_sections`
  and `NON_EMPTY_BULLET_PATTERN`. Existing `validate_task_document`/`validate_task` behaviour, rules
  R1–R6, findings text, and ordering are unchanged. Generation reuses the pure
  `validate_task_document(task_id, text)` function and never calls the printing/file-reading
  `validate_task()` wrapper.
- **Task validation before extraction**: generation safely reads and UTF-8-decodes `task.md`, calls
  `validate_task_document(task_id, text)`, and if any R1–R6 finding exists prints one deterministic
  `error: invalid task document: ...` message, exits 1, and creates no output. Only after successful
  validation do the additive extractors read `Goal`, `Allowed Patterns`, and `Verification Commands`.
  Generation then trims the extracted `Goal`'s leading/trailing blank lines and requires
  non-whitespace content: **R1–R6 guarantee that the `Goal` section exists; TASK-0006 additionally
  requires the extracted `Goal` body to contain non-whitespace text.** An existing but empty or
  whitespace-only `Goal` is exit 1, a deterministic invalid-task-contract error, and creates no
  output; this semantic check does not change existing R1–R6 validation behaviour. This is Task
  Contract structural validation only; Approval-hash, Approval-Chain, Scope, command execution,
  Evidence, and Candidate Snapshot remain deferred to TASK-0009.
- Required primary input artifacts (first supported vertical slice), each read repository-root-relative
  to `cwd`: `.ai/tasks/<TASK-ID>/task.md`, `.ai/tasks/<TASK-ID>/plan.md`,
  `.ai/tasks/<TASK-ID>/approval.md`. A missing, non-regular, unreadable, or non-UTF-8 primary
  artifact, or a Task directory whose resolved real path escapes the Repository, is exit 2.
- Handoff Contract v1 written to `handoff.json` expresses exactly, in fixed key order:
  `schema_version` (integer `1`), `task_id`, `handoff_id` (caller-supplied; never randomly
  generated), `from_role`, `to_role`, `agent_adapter` (label only), `input_artifacts`,
  `context_manifest` (inline versioned structure), `allowed_paths`, `verification_commands`,
  `artifact_digest`, `status` (one generated initial value; no lifecycle), `failure_return_state`.
- `allowed_paths` and `verification_commands` are deterministically extracted from the validated
  `task.md` (`Allowed Patterns` and `Verification Commands` sections), not re-entered through CLI
  arguments.
- Context Manifest v1 (inline in `handoff.json`, no duplicate manifest file): a versioned object
  whose entries each contain `path`, `reason`, `sha256`, `byte_count`. Entries cover the three
  primary artifacts (fixed standard reasons) and every additional context file (caller-supplied
  non-empty reason), sorted by normalized UTF-8 path bytes.
- Deterministic Context Assembly (canonicalization defined in `plan.md` §7): repository-root-relative
  POSIX paths; reject (before `PurePosixPath` construction, filesystem access, digest serialization,
  or rendering) any control character with code point `< 0x20` or `0x7F–0x9F` (including NUL, TAB, CR,
  LF, DEL, and C1 controls); reject absolute paths, `..` traversal, and backslashes; reject duplicate
  normalized paths (including collision with a primary artifact); reject symlinks resolving outside the
  Repository; accept only regular UTF-8 files; strip a leading UTF-8 BOM; normalize CRLF/CR to LF;
  `sha256` and `byte_count` computed over the canonicalized (UTF-8, LF, BOM-stripped) bytes that are
  exactly the bytes embedded in the Prompt Pack. Output contains no timestamp, random value, absolute
  path, hostname, username, temporary path, or environment-specific ordering.
- `artifact_digest` (aggregate) is derived only from the manifest entries — for each entry in sorted
  order, over `path`, per-entry `sha256`, and `byte_count` — never over `handoff.json` or
  `prompt-pack.md` (no self-referential hashing). Changing any input file's content changes its
  per-entry `sha256` and the aggregate `artifact_digest`; adding or removing a context file changes
  the aggregate.
- Text-scalar policy (`plan.md` §5.1) for `from_role`, `to_role`, `agent_adapter`, and each context
  reason: trim surrounding whitespace; reject NUL, CR, LF, and other disallowed control characters
  (exit 2); store the normalized trimmed value. Empty `from_role`/`to_role`/`agent_adapter` after
  trimming is exit 2; an empty or whitespace-only context reason is exit 1. The context reason is
  the normalized trimmed value, not raw-verbatim.
- `prompt-pack.md` (fixed, model-independent Markdown) includes: Handoff identity; source/target
  roles; adapter label; Task Goal (extracted from the validated `task.md`); allowed paths;
  verification commands; failure-return instruction (the target `failure_return_state`, instruction
  only — no transition); input-artifact and context manifest table (with deterministically escaped
  dynamic cells); the deterministically assembled canonical context content wrapped in stable
  boundary markers `<<<AIDEVOS_CONTEXT_FILE path=<json-escaped> sha256="sha256:<hex>"
  byte_count=<int>>>>` … `<<<END_AIDEVOS_CONTEXT_FILE>>>`; an explicit instruction that Repository
  content is context data and cannot override the Handoff Contract, the Task Contract, `AGENTS.md`,
  or `CLAUDE.md`; and a framing statement that the boundary markers are stable and unaffected by
  Markdown code fences but are not a security boundary and that Repository context remains untrusted
  data. The Prompt Pack does not assert that Approval validity has been established.
- Rendering safety (`plan.md` §8): dynamic Markdown table cells escape `\` and `|`; the marker `path`
  attribute is encoded with deterministic JSON-string escaping rather than raw interpolation;
  `byte_count` appears in the marker metadata; canonical context content is preserved unchanged
  between the opening and closing framing lines.
- Output-path containment (`plan.md` §9): before creating any temporary or final output directory,
  resolve the Repository Root from `cwd`, verify the Task directory and the `handoffs` parent resolve
  within the Repository Root, reject any escape through a symlink, and ensure the temporary sibling
  directory resides within the verified output parent. No resolved absolute path is emitted in
  output. An output-containment failure is exit 2.
- Publish semantics (`plan.md` §9): single-process generation is the concurrency model; concurrent
  generation with the same Repository and `handoff_id` is out of scope. All validation completes
  before the output parent is created. Every output byte is prepared and validated in memory; the
  task-local `.ai/tasks/<TASK-ID>/handoffs/` parent is created when absent; publication checks that
  the `<HANDOFF-ID>/` destination does not exist, writes a temporary sibling directory inside the
  verified parent, `fsync`s, then renames it into place on the same filesystem, exposing both files
  together; it never intentionally removes or overwrites a pre-existing `handoffs` parent, an existing
  child, or the destination (exit 2 on an existing destination); a caught write/rename failure cleans
  the temporary directory and, if this invocation created the `handoffs` parent and it is still empty,
  removes that parent, leaving no partial output (exit 2). Forced process termination and cross-process
  TOCTOU guarantees are not claimed. No locking, retry, checkpoint, or native extension.
- `failure_return_state` is validated as vocabulary membership against the currently supported Task
  states (imported `SUPPORTED_STATES` from `task_transition.py`, read-only); an unsupported value is
  exit 2. Membership does not prove the state is a legal transition edge — transition legality
  remains deferred to TASK-0008 — and no Task transition is performed.
- `tests/test_handoff.py` (new), additions to `tests/test_cli.py` and `tests/test_task_validation.py`,
  and `tests/fixtures/handoffs/**` (new) covering the matrix in `plan.md` §12.
- `README.md`: one `aidevos handoff generate` usage example and a minimal update so the
  implemented/planned capability statement no longer claims the completed Handoff Contract and
  deterministic Context Assembly feature is unbuilt.
- This task's own governance records under `.ai/tasks/TASK-0006/**`.

## Non-Goals

- No external Agent or model invocation; no OpenAI/Anthropic/Google/Codex/Claude/Gemini or other SDK
  integration; `agent_adapter` is a descriptive label and is never imported or called.
- No Adapter interface, plugin system, abstract base class framework, template engine, role-specific
  prompt library, vendor-specific prompt syntax, or generic workflow engine (owned by TASK-0007).
- No Handoff lifecycle state machine or Handoff state transitions; `status` has one generated initial
  value. No checkpoint, retry, idempotency lifecycle, resume, recovery, locking, or native concurrency
  extension (owned by TASK-0008).
- No Approval-Decision, Approval-hash, Task-hash, Plan-hash, approver-authority, or Approval-Chain
  validation; no Scope/Allowed-Paths enforcement; no verification command execution; no Evidence
  generation; no Candidate Snapshot integration (owned by TASK-0009). `approval.md` is read as a
  required primary input for its safe bytes only, and the Prompt Pack does not claim Approval validity.
- No transition-edge legality check on `failure_return_state` (membership only; edge legality is
  TASK-0008). No Task transition performed by this command.
- No automatic role routing, Workflow Runner, daemon, Dashboard, Web UI, cloud service, or plugin
  marketplace.
- No context ranking, relevance scoring, token counting/budget optimization, automatic pruning,
  embeddings, RAG, vector database, or Repository-wide implicit file discovery — context is explicit
  allowlist only.
- No second overlapping source contract (no `handoff-request.json`); no duplicate on-disk context
  manifest file. No `.ai/prompts/` directory. No Git-root discovery — `cwd` is the declared
  Repository Root.
- No commit, push, branch, worktree, PR, merge, tag, or Git history change; no mutation outside the
  task-local `.ai/tasks/<TASK-ID>/handoffs/` output area. No new runtime dependency;
  `[project.dependencies]` stays
  empty. No change to `task_transition.py` (imported read-only) or to existing `task_validation.py`
  validation behaviour. No JSON/YAML parser dependency; the standard library only.

## Acceptance Criteria

- [ ] AC-1: Given a Task directory whose `task.md` passes R1–R6 and which contains `plan.md` and
  `approval.md`, `aidevos handoff generate <TASK-ID> --handoff-id <ID> --from-role <R1> --to-role
  <R2> --agent-adapter <A> --failure-return-state IMPLEMENTING` exits 0 and creates exactly
  `.ai/tasks/<TASK-ID>/handoffs/<ID>/handoff.json` and `.ai/tasks/<TASK-ID>/handoffs/<ID>/prompt-pack.md`.
- [ ] AC-2: `handoff.json` contains every required field with correct semantics — `schema_version`
  is the integer `1`; `handoff_id` equals the caller-supplied value (not randomly generated);
  `agent_adapter` is the normalized label; `status` is the single generated initial value; and
  `task_id`, `from_role`, `to_role`, `input_artifacts`, `context_manifest`, `allowed_paths`,
  `verification_commands`, `artifact_digest`, `failure_return_state` are all present.
- [ ] AC-3: `allowed_paths` equals the `Allowed Patterns` bullets, `verification_commands` equals the
  `Verification Commands` bullets, and the Prompt Pack Goal equals the `Goal` body — all extracted
  from the validated `task.md`, never taken from a CLI argument.
- [ ] AC-4: Two independent Repository Roots containing byte-identical inputs, invoked with the same
  `handoff_id` and identical semantic arguments, produce byte-identical corresponding `handoff.json`
  and `prompt-pack.md`.
- [ ] AC-5: Two independent Repository Roots containing byte-identical inputs, invoked with the same
  `handoff_id` and same context set supplied in different `--context` orders, produce byte-identical
  corresponding outputs.
- [ ] AC-6: Any canonical content change changes the per-file `sha256` and aggregate
  `artifact_digest`. `byte_count` always equals `len(canonical_bytes)` and changes only when canonical
  byte length changes. Verified with two cases: (a) a same-length content mutation changes `sha256`
  and `artifact_digest` while `byte_count` stays equal; (b) a different-length mutation changes
  `sha256`, `artifact_digest`, and the accurate `byte_count`.
- [ ] AC-7: When `task.md` has any R1–R6 finding — covering at least missing `Goal`, missing
  `Allowed Patterns`, missing `Verification Commands`, malformed/absent title, a title Task ID that
  mismatches the argument, and a duplicated required section — or when `task.md` is R1–R6-valid but
  its `Goal` body is empty or whitespace-only after trimming, the command prints one deterministic
  `error: invalid task document: ...`, exits 1, and creates no output. R1–R6 validation uses the pure
  `validate_task_document` (never the printing `validate_task` wrapper); the non-empty-`Goal` check is
  a Handoff-specific semantic check that does not alter R1–R6 behaviour.
- [ ] AC-8: A `--context` entry that is unsafe — a path containing a control character (code point
  `< 0x20` or `0x7F–0x9F`, tested at least LF, TAB, and NUL), an absolute path, a path containing
  `..`, a path containing a backslash, a symlink resolving outside the Repository, a non-regular
  file, or a non-UTF-8 file — exits 2 with one deterministic single-line stderr message, empty
  stdout, and no output or temporary directory.
- [ ] AC-9: Two `--context` entries whose paths normalize to the same repository-relative path, or a
  `--context` path colliding with a primary artifact, exit 1 with a deterministic duplicate-path
  message and produce no output.
- [ ] AC-10: A `--context` entry with an empty or whitespace-only reason exits 1 with a deterministic
  empty-reason message and produces no output.
- [ ] AC-11: A missing required primary artifact (e.g. `approval.md` absent), a non-regular or
  unreadable primary artifact, or a required primary or `--context` file that is not valid UTF-8
  exits 2 with a deterministic missing-file / decoding-error message and produces no output.
- [ ] AC-12: `--failure-return-state <STATE>` outside the supported Task states (`INBOX`, `PLANNING`,
  `AWAITING_APPROVAL`, `APPROVED`, `IMPLEMENTING`, `READY_FOR_REVIEW`, `APPROVED_FOR_COMMIT`,
  `COMPLETED`, `REJECTED`, `CANCELLED`) exits 2 with a deterministic message and performs no Task
  transition; a supported value is accepted. Membership does not assert transition-edge legality.
- [ ] AC-13: Text-scalar and rendering safety — `from_role`, `to_role`, `agent_adapter`, and each
  context reason are trimmed and rejected (exit 2) when they contain NUL, CR, LF, or another
  disallowed control character; an empty `from_role`/`to_role`/`agent_adapter` after trimming exits 2;
  Markdown table cells escape `\` and `|` and the marker `path` attribute is JSON-string escaped, so a
  reason containing `|` or `\` and a context path requiring escaping still yield deterministic,
  byte-identical, re-parseable output.
- [ ] AC-14: Output-path containment — a `.ai/tasks/<TASK-ID>/handoffs` path or a Task directory whose
  resolved real path escapes the Repository Root via a symlink exits 2, produces no output, and
  creates no file or directory outside the Repository Root.
- [ ] AC-15: Publish semantics — with the `handoffs` parent initially absent, a first success creates
  the parent and exactly the two files `handoff.json` and `prompt-pack.md` in the final
  `<HANDOFF-ID>/` directory, exposed together; an existing destination directory (empty or non-empty)
  is never overwritten (exit 2) and is byte-identical afterward; and a simulated handled write/rename
  failure leaves no temporary directory and, when this invocation created an initially-absent
  `handoffs` parent, removes that parent (it is still empty), leaving no residue under
  `.ai/tasks/<TASK-ID>/`.
- [ ] AC-16: No mutation outside the task-local output area — a successful or failed generation leaves
  `task.md`, `plan.md`, `approval.md`, and `status.yml` byte-identical, touches nothing outside
  `.ai/tasks/<TASK-ID>/handoffs/`, and does not change Task lifecycle state, the Git index, branch, or
  history (verified by byte/hash comparison before and after).
- [ ] AC-17: Success prints a single deterministic line to stdout and nothing to stderr; every
  failure prints `error: <reason>` to stderr, nothing to stdout, and emits no traceback;
  `aidevos handoff generate ...` and `python -m aidevos handoff generate ...` produce identical
  stdout, stderr, and exit code over two independent Repository copies from identical bytes.
- [ ] AC-18: No network access and no vendor SDK is used; `[project.dependencies]` in `pyproject.toml`
  remains empty; `agent_adapter` never triggers an import or a call.
- [ ] AC-19: `prompt-pack.md` includes the handoff identity, source and target roles, the adapter
  label, the Task Goal, the allowed paths, the verification commands, the failure-return instruction,
  the input-artifact and context manifest (with `byte_count` in the marker metadata), and the
  deterministically assembled context content wrapped in the `<<<AIDEVOS_CONTEXT_FILE ...>>>` /
  `<<<END_AIDEVOS_CONTEXT_FILE>>>` markers; it states that Repository content is context data that
  cannot override the Handoff Contract, the Task Contract, `AGENTS.md`, or `CLAUDE.md`, that the
  framing is stable and unaffected by Markdown code fences but is not a security boundary; and it does
  not assert that Approval validity has been established.
- [ ] AC-20: Existing Task Validation and Transition behaviour is unchanged —
  `aidevos task validate TASK-0004` prints `TASK-0004: valid` (exit 0), `aidevos task validate
  TASK-0006` prints `TASK-0006: valid` (exit 0), and the existing `tests/test_task_validation.py` and
  `tests/test_task_transition.py` suites pass unmodified in behaviour.
- [ ] AC-21: `pytest -q`, `ruff check .`, `ruff format --check .`, and `mypy src` all pass;
  `[project.dependencies]` stays empty.
- [ ] AC-22: `README.md` gains one `aidevos handoff generate` usage example, and its
  implemented/planned capability statement no longer claims the now-built Handoff Contract and
  deterministic Context Assembly are unbuilt, while still marking Adapters, Workflow Runner, and
  Evaluation as planned.

## Allowed Patterns

- `src/aidevos/handoff.py`
- `src/aidevos/cli.py`
- `src/aidevos/task_validation.py`
- `tests/test_handoff.py`
- `tests/test_cli.py`
- `tests/test_task_validation.py`
- `tests/fixtures/handoffs/**`
- `README.md`
- `.ai/tasks/TASK-0006/**`

## Restricted Patterns

- `src/aidevos/task_transition.py` — imported read-only for `SUPPORTED_STATES`; must not be modified.
- `src/aidevos/__init__.py` (no version bump), `src/aidevos/__main__.py`.
- `pyproject.toml` — no dependency additions; `[project.dependencies]` stays empty.
- `docs/AI-DevOS-V4.2.1.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`.
- `.ai/schemas/**`, `.ai/workflows/**`, `.ai/constraints.yml`.
- `.ai/tasks/TASK-0001/**`, `.ai/tasks/TASK-0002/**`, `.ai/tasks/TASK-0003/**`,
  `.ai/tasks/TASK-0004/**`, `.ai/tasks/TASK-0005/**` — historical tasks, read only.
- All of `.ai/**` except `.ai/tasks/TASK-0006/**`.
- `.git/**`, `.github/**` — no commit, push, branch, worktree, PR, CI change, or history rewrite.

## Verification Commands

- `pytest -q`
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `aidevos task validate TASK-0006` (expect: `TASK-0006: valid`, exit 0)
- `aidevos task validate TASK-0004` (expect: `TASK-0004: valid`, exit 0 — no regression)
- `aidevos --version` (expect: `0.1.0`, exit 0)
- `python -m aidevos task validate TASK-0006` (parity check)

## Dependencies

- Baseline commit: `42b55ea`. TASK-0001, TASK-0002, TASK-0003, TASK-0004, and TASK-0005 are
  COMPLETED on `main`; no task dependencies remain. The planned implementation branch
  `feature/task-0006` is not created during planning. TASK-0006 depends only on the existing CLI /
  argparse, the imported `SUPPORTED_STATES` constant, the pure `validate_task_document` function, and
  the Python standard library; it introduces no runtime dependency.

## Risks

- **Non-determinism leaking into output** — a stray timestamp, absolute path, dict-ordering, or CRLF
  difference would break byte-for-byte reproducibility (AC-4/AC-5). Mitigation: fixed JSON key order
  with `indent=2` and `ensure_ascii=False`, a trailing newline, sorting manifest entries by
  normalized path bytes, canonicalizing content to LF, and forbidding any host/user/time/random/abs
  value in output.
- **Extracting from an invalid Task** — extracting `Goal`/`Allowed Patterns`/`Verification Commands`
  from a malformed `task.md` would yield a misleading, empty, or inconsistent contract. Mitigation:
  run the pure `validate_task_document` first; any R1–R6 finding is exit 1 with no output (AC-7).
- **Over-claiming Approval or mutation** — the generator writes an artifact and does not verify
  Approval validity. Mitigation: accurate boundary wording (writes only the output directory; reads
  `approval.md` for bytes only; no Decision/hash/chain validation), and a Prompt Pack that does not
  assert Approval validity (Background, Scope, AC-16/AC-19).
- **Self-referential hashing** — hashing `handoff.json` into its own `artifact_digest` would be
  unstable. Mitigation: `artifact_digest` is derived only from manifest entries (path + per-entry
  sha256 + byte_count), never from the emitted files.
- **Path-safety escape (input and output)** — absolute paths, `..`, backslashes, or symlinks could
  read or write outside the Repository. Mitigation: reject absolute/`..`/backslash, normalize, then
  require the resolved real path to stay within the resolved Repository Root for inputs, the Task
  directory, and the `handoffs` output parent; accept only regular UTF-8 files (AC-8/AC-11/AC-14).
- **Prompt-rendering injection / breakage** — a control character, `|`, `\`, or quote in a role,
  adapter, reason, or path could corrupt the Markdown table or marker line. Mitigation: a single
  text-scalar policy (trim, reject control chars, require non-empty per field) plus deterministic
  cell/marker escaping; the framing is documented as stable but explicitly not a security boundary
  (AC-13/AC-19).
- **Partial output or overwrite on failure** — a crash mid-write or an existing directory could leave
  a half-written or clobbered handoff. Mitigation: prepare all bytes in memory, containment-check,
  refuse an existing destination, write a temporary sibling directory, `fsync`, atomically rename;
  clean the temp directory on any caught failure; single-process concurrency model, no TOCTOU claim
  (AC-14/AC-15).
- **Scope creep toward Adapter/Runner/Eval** — the temptation to invoke models, enforce scope,
  validate hashes, or add a lifecycle. Mitigation: `agent_adapter` is a label; `status` is one value;
  `failure_return_state` is membership-validated but never transitioned; explicit deferral to
  TASK-0007/0008/0009 (`plan.md` §14).
- **Duplicating the Markdown parser** — a second parser would drift from the validator. Mitigation:
  reuse `_parse_sections`/`NON_EMPTY_BULLET_PATTERN` via an additive extractor in
  `task_validation.py`; existing validation behaviour is untouched (AC-20).
- **Dependency creep** — `[project.dependencies]` stays empty; JSON via the stdlib `json` module,
  hashing via `hashlib` (AC-18/AC-21).
- **Self-consistency of this Task's own contract** — `aidevos task validate TASK-0006` must pass;
  this `task.md` follows the §8 section schema exactly (AC-20).

## Rollback Notes

- Pre-approval: if rejected or cancelled, advance TASK-0006 only through a legal state transition to
  `REJECTED` or `CANCELLED`; retain `task.md`, `plan.md`, `status.yml`, the decision reason, and audit
  history. Do not delete the task directory. No implementation exists during planning.
- Post-implementation: delete `src/aidevos/handoff.py`, `tests/test_handoff.py`, and
  `tests/fixtures/handoffs/`; revert `src/aidevos/cli.py`, `src/aidevos/task_validation.py`,
  `tests/test_cli.py`, `tests/test_task_validation.py`, and `README.md` to baseline `42b55ea`.
  Because the generator only writes under `.ai/tasks/<TASK-ID>/handoffs/`, any generated handoff
  directory can be removed with no effect on Task state, `status.yml`, or Git history.
- Preserve `.ai/tasks/TASK-0006/**` after approval as governance and audit history. No historical
  task file, `docs/`, `pyproject.toml`, package version, `task_transition.py`, or Git state is
  changed by an implementation rollback. No database, runtime, or deployment rollback is involved.
