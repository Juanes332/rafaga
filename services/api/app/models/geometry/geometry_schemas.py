"""Pydantic models of the geometry domain."""

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

Point = Annotated[list[float], Field(min_length=2, max_length=2)]
Ring = Annotated[list[Point], Field(min_length=3)]
IssueCode = Literal[
    "not_closed", "self_intersection", "height_out_of_range",
    "footprint_too_small", "missing_height", "overlap",
]


def signed_area(ring: list[list[float]]) -> float:
    """Return the shoelace area, positive for counter-clockwise rings."""
    return sum(
        a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1])
    ) / 2


def normalize_ring(ring: list[list[float]], ccw: bool) -> list[list[float]]:
    """Drop a repeated closing vertex and enforce the winding order."""
    if len(ring) > 3 and ring[0] == ring[-1]:
        ring = ring[:-1]
    if (signed_area(ring) > 0) != ccw and signed_area(ring) != 0:
        ring = ring[::-1]
    return ring


class Tier(BaseModel):
    """One stacked slice of a building."""

    z_from: float = Field(ge=0)
    z_to: float
    footprint: Ring

    @field_validator("footprint")
    @classmethod
    def _ccw(cls, ring: list[list[float]]) -> list[list[float]]:
        """Normalize the tier footprint."""
        return normalize_ring(ring, True)


class Building(BaseModel):
    """A building: footprint prism with optional tiers."""

    id: UUID
    name: str | None = Field(default=None, max_length=80)
    footprint: Ring
    holes: list[Ring] = []
    height_m: float | None
    tiers: list[Tier] | None = None
    source: Literal["draw", "dxf", "stl", "obj", "ifc", "trace"]
    missing_height: bool = False

    @field_validator("footprint")
    @classmethod
    def _outer(cls, ring: list[list[float]]) -> list[list[float]]:
        """Normalize the outer ring to CCW without closing vertex."""
        return normalize_ring(ring, True)

    @field_validator("holes")
    @classmethod
    def _holes(cls, rings: list[list[list[float]]]) -> list[list[list[float]]]:
        """Normalize hole rings to CW without closing vertex."""
        return [normalize_ring(r, False) for r in rings]

    def to_json(self) -> dict[str, Any]:
        """Return the jsonb form, omitting absent tiers."""
        data = self.model_dump(mode="json")
        if data["tiers"] is None:
            del data["tiers"]
        return data


class GeometryIssue(BaseModel):
    """A validation finding about one building."""

    building_id: UUID | None = None
    code: IssueCode
    message_key: str
    location: Point | None = None


class GeometryResponse(BaseModel):
    """The Geometry schema of openapi.yaml."""

    version: int
    buildings: list[Building]
    issues: list[GeometryIssue]
    orphaned_elements: list[UUID] = []


class GeometryPutRequest(BaseModel):
    """Body of PUT /geometry."""

    expected_version: int = Field(ge=1)
    confirm_base_change: bool = False
    buildings: list[Building] = Field(max_length=2000)


class GeometryValidateRequest(BaseModel):
    """Body of POST /geometry/validate."""

    buildings: list[Building] | None = None


class GeometryValidationResponse(BaseModel):
    """Body of the validate response."""

    issues: list[GeometryIssue]


class IgnoredEntity(BaseModel):
    """An entity skipped by an importer."""

    entity: str
    reason: str


class ImportReportResponse(BaseModel):
    """The ImportReport schema of openapi.yaml."""

    buildings_added: int
    missing_height: list[UUID]
    ignored: list[IgnoredEntity]
    detected_unit: Literal["m", "cm", "mm", "ft", "unknown"]
    warnings: list[str]
    geometry: GeometryResponse | None = None
