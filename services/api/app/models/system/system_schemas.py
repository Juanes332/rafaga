"""Pydantic models of the system domain."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Body of GET /health."""

    status: Literal["ok", "degraded"]
    db: Literal["ok", "down"]
    version: str


class SolverStatus(BaseModel):
    """Capabilities of the freshest solver node."""

    online: bool
    device: Literal["cpu", "gpu"] | None = None
    gpu_name: str | None = None
    vram_total_bytes: int | None = None
    ram_budget_bytes: int | None = None
    cpu_cores: int | None = None
    mlups_2d: float | None = None
    mlups_3d: float | None = None
    heartbeat_at: datetime | None = None


class SystemStatusResponse(BaseModel):
    """Body of GET /api/v1/system/status."""

    api: Literal["ok"] = "ok"
    db: Literal["ok", "down"]
    solver: SolverStatus
