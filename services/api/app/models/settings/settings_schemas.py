"""Pydantic models of the settings domain."""

from typing import Self

from pydantic import BaseModel, Field, model_validator


class Thresholds(BaseModel):
    """Zone thresholds on the amplification factor K."""

    k_accel: float = Field(default=1.2, gt=0)
    k_stagnation: float = Field(default=0.3, gt=0)
    dk_reduction: float = Field(default=-0.1, le=0)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        """Require k_accel > k_stagnation > 0."""
        if self.k_accel <= self.k_stagnation:
            raise ValueError("k_accel must exceed k_stagnation")
        return self


class LawsonClass(BaseModel):
    """One comfort class; the last one has no upper threshold."""

    key: str
    label_key: str
    threshold_ms: float | None


class LawsonSafety(BaseModel):
    """One safety limit."""

    key: str
    label_key: str | None = None
    threshold_ms: float


def _default_comfort() -> list[LawsonClass]:
    """Return the ADR-15 comfort classes."""
    rows = [("sitting", 4), ("standing", 6), ("strolling", 8),
            ("business_walking", 10), ("uncomfortable", None)]
    return [LawsonClass(key=k, label_key=f"lawson.{k}", threshold_ms=t) for k, t in rows]


def _default_safety() -> list[LawsonSafety]:
    """Return the ADR-15 safety limits."""
    rows = [("unsafe_frail", 15), ("unsafe_all", 20)]
    return [LawsonSafety(key=k, label_key=f"lawson.{k}", threshold_ms=t) for k, t in rows]


def _increasing(values: list[float]) -> bool:
    """Return whether values are strictly increasing."""
    return all(a < b for a, b in zip(values, values[1:], strict=False))


class LawsonTable(BaseModel):
    """The editable Lawson LDDC table."""

    exceedance_probability: float = Field(default=0.05, gt=0, lt=1)
    comfort: list[LawsonClass] = Field(default_factory=_default_comfort, min_length=2)
    safety_probability: float = Field(default=0.00025, gt=0, lt=1)
    safety: list[LawsonSafety] = Field(default_factory=_default_safety, min_length=1)

    @model_validator(mode="after")
    def _thresholds_increase(self) -> Self:
        """Require strictly increasing thresholds, open class last."""
        limits = [c.threshold_ms for c in self.comfort]
        if limits[-1] is not None or None in limits[:-1] or not _increasing(limits[:-1]):
            raise ValueError("comfort thresholds must increase, last class open")
        if not _increasing([s.threshold_ms for s in self.safety]):
            raise ValueError("safety thresholds must increase")
        return self


class SettingsResponse(BaseModel):
    """The caller's settings."""

    thresholds: Thresholds
    lawson: LawsonTable
    turbulence_intensity_default: float = Field(ge=0, le=1)
    vegetation_cd: float = Field(ge=0.05, le=1.0)
    alternatives_limit: int = Field(ge=1, le=20)


class SettingsPatchRequest(BaseModel):
    """Body of PATCH /settings; every field optional."""

    thresholds: Thresholds | None = None
    lawson: LawsonTable | None = None
    turbulence_intensity_default: float | None = Field(default=None, ge=0, le=1)
    vegetation_cd: float | None = Field(default=None, ge=0.05, le=1.0)
    alternatives_limit: int | None = Field(default=None, ge=1, le=20)
