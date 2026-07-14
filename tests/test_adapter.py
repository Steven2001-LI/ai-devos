from __future__ import annotations

import ast
import copy
import json
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

import aidevos.adapter as adapter_module
from aidevos.adapter import (
    ADAPTER_CONTRACT_VERSION,
    AdapterError,
    AdapterPayload,
    AdapterRequest,
    InvalidAdapterInput,
    UnsupportedContractVersion,
    build_adapter_payload,
)


ADAPTER_SOURCE = Path(adapter_module.__file__).read_text(encoding="utf-8")


def valid_contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "task_id": "TASK-0007",
        "context_manifest": {
            "manifest_version": 1,
            "entries": [{"path": "文档.md", "byte_count": 7}],
        },
        "flags": [True, False, None, 3, 1.5],
    }


def test_builder_is_the_validated_construction_path_without_constructor_guard() -> None:
    payload = build_adapter_payload(AdapterRequest(valid_contract(), "Instructions\n"))
    direct = AdapterPayload(99, "", b"not validated JSON")

    assert payload.adapter_contract_version == ADAPTER_CONTRACT_VERSION
    assert direct == AdapterPayload(99, "", b"not validated JSON")
    assert [field.name for field in fields(AdapterPayload)] == [
        "adapter_contract_version",
        "instructions",
        "canonical_handoff_json",
    ]


def test_module_defines_no_protocol_abc_or_execution_api() -> None:
    forbidden_symbols = {
        "Protocol",
        "ABC",
        "run",
        "execute",
        "invoke",
        "dispatch",
        "route",
        "retry",
        "resume",
    }

    assert forbidden_symbols.isdisjoint(vars(adapter_module))
    assert not any(name in forbidden_symbols for name in vars(AdapterPayload))


def test_production_imports_are_limited_and_dependencies_remain_empty() -> None:
    tree = ast.parse(ADAPTER_SOURCE)
    imported_modules = {
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module not in (None, "__future__")
    }
    imported_modules.update(
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert imported_modules == {"collections", "dataclasses", "json", "math"}
    assert "dependencies = []" in pyproject
    assert "aidevos.handoff" not in ADAPTER_SOURCE
    assert "aidevos.cli" not in ADAPTER_SOURCE


def test_payload_is_frozen_and_contains_only_immutable_scalar_values() -> None:
    payload = build_adapter_payload(AdapterRequest(valid_contract(), "Instructions"))

    assert tuple(type(getattr(payload, field.name)) for field in fields(payload)) == (
        int,
        str,
        bytes,
    )
    with pytest.raises(FrozenInstanceError):
        payload.instructions = "changed"  # type: ignore[misc]


def test_equal_input_produces_equal_payload() -> None:
    first = build_adapter_payload(AdapterRequest(valid_contract(), "Instructions\r\n"))
    second = build_adapter_payload(
        AdapterRequest(copy.deepcopy(valid_contract()), "Instructions\r\n")
    )

    assert first == second
    assert first.canonical_handoff_json == second.canonical_handoff_json


def test_canonical_json_is_order_independent_compact_utf8_and_round_trips() -> None:
    first_contract = {
        "schema_version": 1,
        "nested": {"z": 2, "a": "你好"},
        "alpha": [1, True, None],
    }
    second_contract = {
        "alpha": [1, True, None],
        "nested": {"a": "你好", "z": 2},
        "schema_version": 1,
    }

    first = build_adapter_payload(AdapterRequest(first_contract, "Instructions"))
    second = build_adapter_payload(AdapterRequest(second_contract, "Instructions"))

    expected = '{"alpha":[1,true,null],"nested":{"a":"你好","z":2},"schema_version":1}'.encode()
    assert first.canonical_handoff_json == expected
    assert second.canonical_handoff_json == expected
    assert json.loads(first.canonical_handoff_json) == first_contract
    assert b"\\u4f60" not in first.canonical_handoff_json
    assert b" " not in first.canonical_handoff_json


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_floats_are_rejected(value: float) -> None:
    contract = valid_contract()
    contract["value"] = value

    with pytest.raises(InvalidAdapterInput, match="floats must be finite"):
        build_adapter_payload(AdapterRequest(contract, "Instructions"))


@pytest.mark.parametrize(
    "value",
    [
        ("tuple",),
        {"set"},
        frozenset({"frozen"}),
        b"bytes",
        bytearray(b"bytes"),
        object(),
    ],
    ids=["tuple", "set", "frozenset", "bytes", "bytearray", "custom-object"],
)
def test_non_json_values_are_rejected(value: object) -> None:
    contract = valid_contract()
    contract["value"] = value

    with pytest.raises(InvalidAdapterInput, match="unsupported value"):
        build_adapter_payload(AdapterRequest(contract, "Instructions"))


def test_non_string_keys_at_any_depth_are_rejected_without_coercion() -> None:
    contract = valid_contract()
    contract["nested"] = {1: "not silently coerced"}

    with pytest.raises(InvalidAdapterInput, match="keys must be strings"):
        build_adapter_payload(AdapterRequest(contract, "Instructions"))


@pytest.mark.parametrize("kind", ["list", "mapping"])
def test_cyclic_containers_are_rejected_during_materialization(kind: str) -> None:
    contract = valid_contract()
    if kind == "list":
        cyclic_list: list[object] = []
        cyclic_list.append(cyclic_list)
        contract["cyclic"] = cyclic_list
    else:
        cyclic_mapping: dict[str, object] = {}
        cyclic_mapping["self"] = cyclic_mapping
        contract["cyclic"] = cyclic_mapping

    with pytest.raises(InvalidAdapterInput, match="must not contain a cycle"):
        build_adapter_payload(AdapterRequest(contract, "Instructions"))


def test_payload_is_detached_and_builder_does_not_mutate_input() -> None:
    contract = valid_contract()
    before = copy.deepcopy(contract)
    prompt = "  Instructions\r\nwith final line\r"
    request = AdapterRequest(contract, prompt)

    payload = build_adapter_payload(request)
    original_payload = copy.deepcopy(payload)

    assert contract == before
    assert request.prompt_pack_text == prompt
    contract["task_id"] = "TASK-CHANGED"
    manifest = contract["context_manifest"]
    assert isinstance(manifest, dict)
    entries = manifest["entries"]
    assert isinstance(entries, list)
    entries.append({"path": "later.md"})
    assert payload == original_payload
    assert json.loads(payload.canonical_handoff_json) == before


@pytest.mark.parametrize("contract", [[], "mapping", 1, None])
def test_handoff_contract_must_be_a_mapping(contract: object) -> None:
    request = AdapterRequest(contract, "Instructions")  # type: ignore[arg-type]

    with pytest.raises(InvalidAdapterInput, match="must be a mapping"):
        build_adapter_payload(request)


def test_request_must_be_adapter_request() -> None:
    with pytest.raises(InvalidAdapterInput, match="request must be an AdapterRequest"):
        build_adapter_payload(object())  # type: ignore[arg-type]


@pytest.mark.parametrize("version", ["1", [1], {"value": 1}, 1.0, None])
def test_missing_and_wrong_typed_schema_versions_are_invalid(version: object) -> None:
    with pytest.raises(InvalidAdapterInput, match="missing schema_version"):
        build_adapter_payload(AdapterRequest({}, "Instructions"))

    contract = valid_contract()
    contract["schema_version"] = version
    with pytest.raises(InvalidAdapterInput, match="must be an integer"):
        build_adapter_payload(AdapterRequest(contract, "Instructions"))


@pytest.mark.parametrize("version", [True, False])
def test_bool_schema_version_is_invalid_not_unsupported(version: bool) -> None:
    contract = valid_contract()
    contract["schema_version"] = version

    with pytest.raises(InvalidAdapterInput, match="must be an integer"):
        build_adapter_payload(AdapterRequest(contract, "Instructions"))


@pytest.mark.parametrize("version", [0, 2, -1])
def test_real_unsupported_schema_version_has_specific_error(version: int) -> None:
    contract = valid_contract()
    contract["schema_version"] = version

    with pytest.raises(
        UnsupportedContractVersion,
        match=f"unsupported Handoff Contract schema_version: {version}",
    ):
        build_adapter_payload(AdapterRequest(contract, "Instructions"))


def test_adapter_error_family_is_exact_and_library_oriented() -> None:
    assert issubclass(InvalidAdapterInput, AdapterError)
    assert issubclass(UnsupportedContractVersion, AdapterError)
    assert set(AdapterError.__subclasses__()) == {
        InvalidAdapterInput,
        UnsupportedContractVersion,
    }


@pytest.mark.parametrize("prompt", [None, b"text", 1, "", " \t\r\n"])
def test_invalid_prompt_pack_input_is_rejected(prompt: object) -> None:
    request = AdapterRequest(valid_contract(), prompt)  # type: ignore[arg-type]

    with pytest.raises(InvalidAdapterInput):
        build_adapter_payload(request)


@pytest.mark.parametrize("prompt", ["\ufeff", "\ufeff \t\r\n\r"])
def test_bom_only_or_bom_and_whitespace_prompt_is_rejected(prompt: str) -> None:
    with pytest.raises(InvalidAdapterInput, match="must not be empty"):
        build_adapter_payload(AdapterRequest(valid_contract(), prompt))


def test_prompt_normalization_order_and_whitespace_preservation() -> None:
    payload = build_adapter_payload(
        AdapterRequest(valid_contract(), "\ufeff  First\r\nSecond\rThird  \r\n")
    )
    one_bom_only = build_adapter_payload(AdapterRequest(valid_contract(), "\ufeff\ufeffText"))

    assert payload.instructions == "  First\nSecond\nThird  \n"
    assert one_bom_only.instructions == "\ufeffText"
    assert payload.instructions.endswith("  \n")


def test_shared_non_cyclic_container_is_accepted_and_detached() -> None:
    shared = ["one"]
    contract = {"schema_version": 1, "first": shared, "second": shared}

    payload = build_adapter_payload(AdapterRequest(contract, "Instructions"))
    shared.append("later")

    assert json.loads(payload.canonical_handoff_json) == {
        "first": ["one"],
        "schema_version": 1,
        "second": ["one"],
    }
