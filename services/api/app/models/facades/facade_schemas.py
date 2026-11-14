"""Pydantic models of the facades domain."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

FacadeType = Literal["screen", "fins", "canopy", "setback", "vegetation"]


class FacadeElementCreateRequest(BaseModel):
    """Body of POST /alternatives/{id}/facade-elements."""

    building_id: UUID
    edge_index: int = Field(ge=0)
    type: FacadeType
    params: dict[str, Any] = Field(default_factory=dict)


class FacadeElementPatchRequest(BaseModel):
    """Body of PATCH /facade-elements/{id}."""

    params: dict[str, Any]
    confirm_base_change: bool = False


class AdjustmentResponse(BaseModel):
    """A value the server clamped into range."""

    field: str
    requested: float
    applied: float
    reason: str | None = None


class FacadeElementResponse(BaseModel):
    """A facade element on a building edge."""

    id: UUID
    building_id: UUID
    edge_index: int
    type: FacadeType
    params: dict[str, Any]
    orphaned: bool = False


class FacadeElementWithAdjustments(FacadeElementResponse):
    """An element plus the clamping report of the write."""

    adjustments: list[AdjustmentResponse]


class StrategyParameter(BaseModel):
    """One adjustable parameter of a strategy."""

    key: str
    unit: str
    min: float
    max: float
    default: float | None
    help_key: str


class FacadeStrategyResponse(BaseModel):
    """One facade strategy with its parameters."""

    type: FacadeType
    label_key: str
    help_key: str
    parameters: list[StrategyParameter]
