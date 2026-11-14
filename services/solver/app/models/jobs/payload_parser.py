"""Validate raw payload JSON into typed models with contract errors."""

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.errors.solver_errors import ContractVersionMismatchError, InvalidPayloadError

CONTRACT_VERSION = 1
Model = TypeVar("Model", bound=BaseModel)


def parse_payload(model: type[Model], raw: dict[str, Any]) -> Model:
    """Return the typed payload or raise the contract error code."""
    got = raw.get("contract_version") if isinstance(raw, dict) else None
    if got != CONTRACT_VERSION:
        raise ContractVersionMismatchError(
            "unsupported contract_version", {"expected": CONTRACT_VERSION, "got": got}
        )
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        path = ".".join(str(p) for p in first["loc"])
        raise InvalidPayloadError(
            "payload does not satisfy the job contract",
            {"path": path, "reason": first["msg"]},
        ) from exc
