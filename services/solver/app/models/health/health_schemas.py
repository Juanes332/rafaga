"""Response model of GET /health (SOL-01)."""

from typing import Literal

from pydantic import BaseModel


class HeavyLaneState(BaseModel):
    """Heavy lane occupancy."""

    busy: bool
    job_id: str | None


class LightLaneState(BaseModel):
    """Light lane occupancy."""

    busy: bool


class LaneStates(BaseModel):
    """Both lanes."""

    heavy: HeavyLaneState
    light: LightLaneState


class HealthResponse(BaseModel):
    """Solver liveness, device and database reachability."""

    status: Literal["ok", "degraded"]
    device: Literal["cpu", "gpu"]
    gpu_name: str | None
    db: Literal["ok", "down"]
    lanes: LaneStates
