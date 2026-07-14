"""Pure construction of vendor-neutral adapter payloads."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass


ADAPTER_CONTRACT_VERSION = 1
SUPPORTED_HANDOFF_SCHEMA_VERSION = 1


class AdapterError(Exception):
    """Base error for adapter payload construction."""


class InvalidAdapterInput(AdapterError):
    """Raised when adapter input violates the boundary contract."""


class UnsupportedContractVersion(AdapterError):
    """Raised when the Handoff Contract version is well-formed but unsupported."""


@dataclass(frozen=True)
class AdapterRequest:
    """Already-produced Handoff Contract data and Prompt Pack text."""

    handoff_contract: Mapping[str, object]
    prompt_pack_text: str


@dataclass(frozen=True)
class AdapterPayload:
    """Detached, transport-neutral input for a future concrete adapter."""

    adapter_contract_version: int
    instructions: str
    canonical_handoff_json: bytes


def _normalize_prompt_pack(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidAdapterInput("prompt_pack_text must be a string")
    if value.startswith("\ufeff"):
        value = value[1:]
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.strip():
        raise InvalidAdapterInput("prompt_pack_text must not be empty")
    return normalized


def _materialize_json_tree(value: object, active_containers: set[int]) -> object:
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in active_containers:
            raise InvalidAdapterInput("handoff_contract must not contain a cycle")
        active_containers.add(marker)
        try:
            materialized: dict[str, object] = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise InvalidAdapterInput("handoff_contract keys must be strings")
                materialized[key] = _materialize_json_tree(item, active_containers)
            return materialized
        finally:
            active_containers.remove(marker)

    if isinstance(value, list):
        marker = id(value)
        if marker in active_containers:
            raise InvalidAdapterInput("handoff_contract must not contain a cycle")
        active_containers.add(marker)
        try:
            return [_materialize_json_tree(item, active_containers) for item in value]
        finally:
            active_containers.remove(marker)

    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise InvalidAdapterInput("handoff_contract floats must be finite")
        return value
    raise InvalidAdapterInput("handoff_contract contains an unsupported value")


def build_adapter_payload(request: AdapterRequest) -> AdapterPayload:
    """Validate, normalize, detach, and canonicalize one adapter request."""
    if not isinstance(request, AdapterRequest):
        raise InvalidAdapterInput("request must be an AdapterRequest")

    contract = request.handoff_contract
    if not isinstance(contract, Mapping):
        raise InvalidAdapterInput("handoff_contract must be a mapping")
    if "schema_version" not in contract:
        raise InvalidAdapterInput("handoff_contract is missing schema_version")

    schema_version = contract["schema_version"]
    if type(schema_version) is not int:
        raise InvalidAdapterInput("schema_version must be an integer")
    if schema_version != SUPPORTED_HANDOFF_SCHEMA_VERSION:
        raise UnsupportedContractVersion(
            f"unsupported Handoff Contract schema_version: {schema_version}"
        )

    instructions = _normalize_prompt_pack(request.prompt_pack_text)
    try:
        materialized = _materialize_json_tree(contract, set())
        canonical_json = json.dumps(
            materialized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except RecursionError as error:
        raise InvalidAdapterInput("handoff_contract nesting is too deep") from error
    except (TypeError, ValueError, UnicodeError) as error:
        raise InvalidAdapterInput("handoff_contract is not canonical JSON data") from error

    return AdapterPayload(
        adapter_contract_version=ADAPTER_CONTRACT_VERSION,
        instructions=instructions,
        canonical_handoff_json=canonical_json,
    )
