"""Canonical scene primitives (contracts/scene.schema.json) as consumed here."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Point2 = tuple[float, float]


class _Loose(BaseModel):
    """Accept additive contract fields without failing."""

    model_config = ConfigDict(extra="ignore")


class PrimitiveOrigin(_Loose):
    """Where a primitive came from (building or facade element)."""

    kind: str
    building_id: str
    element_id: str | None = None


class Prism(_Loose):
    """Vertical prism: footprint polygon extruded from z_min to z_max."""

    id: str
    origin: PrimitiveOrigin
    footprint: list[Point2] = Field(min_length=3)
    holes: list[list[Point2]] = Field(default_factory=list)
    z_min: float = Field(ge=0)
    z_max: float = Field(le=500)


class Solid(Prism):
    """Impermeable prism."""

    thin_axis_m: float | None = None


class Porous(Prism):
    """Porous screen or vegetation volume."""

    model: Literal["screen", "vegetation"]
    porosity: float | None = None
    loss_coefficient: float | None = None
    normal: Point2 | None = None
    thickness_m: float | None = None
    lad_m2_m3: float | None = None
    drag_coefficient: float | None = None


class SceneWarning(_Loose):
    """Warning emitted by the scene compiler."""

    code: str
    ref: str


class Scene(_Loose):
    """The scene as handed from api to solver."""

    schema_version: Literal["1.0"]
    analysis_height_m: float
    ground: dict
    h_max_m: float = Field(gt=0)
    bounds: dict
    solids: list[Solid]
    porous: list[Porous]
    warnings: list[SceneWarning] = Field(default_factory=list)
    source: dict = Field(default_factory=dict)

    def source_ref(self) -> str:
        """Return the alternative id used as warning ref for scene-wide notes."""
        return str(self.source.get("alternative_id", "scene"))
