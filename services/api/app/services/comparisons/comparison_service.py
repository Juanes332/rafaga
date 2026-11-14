"""Comparisons domain business logic (BR-11)."""

from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.result_errors import ResultsIncomparableError
from app.models.comfort.comfort_schemas import ComfortResponse
from app.security.jwt.jwt_guard import CurrentUser
from app.services.comfort.comfort_service import ComfortService, get_comfort_service
from app.services.comfort.lawson_service import caller_settings
from app.services.results.result_files import load_field
from app.services.results.result_service import ResultService, get_result_service
from app.services.results.zone_calculator import compute_zones, fluid_area, reduction_zone

FIELD_MAP = {"kind": "kind", "direction_deg": "direction", "z0_m": "z0", "uref_za_ms": "u_ref",
             "dx_m": "dx", "output_grid": "grid", "analysis_height_m": "analysis_height",
             "section": "section"}


def differences(a: dict[str, Any], b: dict[str, Any]) -> list[dict[str, Any]]:
    """Itemise the comparability fields that differ."""
    return [{"field": name, "a": a["comparability"].get(key), "b": b["comparability"].get(key)}
            for key, name in FIELD_MAP.items()
            if a["comparability"].get(key) != b["comparability"].get(key)]


class ComparisonService:
    """Check comparability and compute comparative areas and comfort."""

    def __init__(self, session: AsyncSession, results: ResultService, comfort: ComfortService) -> None:
        """Bind collaborators."""
        self._session, self._results, self._comfort = session, results, comfort

    async def pair(self, user: CurrentUser, a: UUID, b: UUID) -> tuple[dict, dict]:
        """Load two readable results and require equal comparability keys."""
        ra, rb = await self._results.load(user, a), await self._results.load(user, b)
        if ra["comparability_key"] != rb["comparability_key"]:
            raise ResultsIncomparableError(details={"differences": differences(ra, rb)})
        return ra, rb

    async def areas(self, user: CurrentUser, a: UUID, b: UUID, k_accel: float | None,
                    k_stagnation: float | None, dk: float | None) -> dict[str, Any]:
        """Return zone areas of both results plus the reduction area."""
        ra, rb = await self.pair(user, a, b)
        th = (await caller_settings(self._session, user.id))["thresholds"]
        ka, ks, dk = k_accel or th["k_accel"], k_stagnation or th["k_stagnation"], dk or th["dk_reduction"]
        settings = self._results._settings
        karr, barr = load_field(settings, ra, "K"), load_field(settings, rb, "K")
        dx = ra["dx_m"]

        def zones(row: dict, arr: Any) -> dict[str, Any]:
            return {"result_id": row["id"], "thresholds": {"k_accel": ka, "k_stagnation": ks},
                    "fluid_area_m2": fluid_area(arr, dx), "zones": compute_zones(arr, dx, ka, ks)}

        return {"a": zones(ra, karr), "b": zones(rb, barr), "reduction": reduction_zone(karr, barr, dx, dk),
                "thresholds": {"k_accel": ka, "k_stagnation": ks, "dk_reduction": dk}}

    async def comfort(self, user: CurrentUser, a: UUID, b: UUID) -> dict[str, ComfortResponse]:
        """Return both studies' comfort when they share project and kind."""
        sa, sb = await self._comfort.study(user, a), await self._comfort.study(user, b)
        if sa["project_id"] != sb["project_id"] or sa["kind"] != sb["kind"]:
            raise ResultsIncomparableError(
                details={"differences": [{"field": "kind", "a": sa["kind"], "b": sb["kind"]}]})
        return {"a": await self._comfort.get(user, a), "b": await self._comfort.get(user, b)}


def get_comparison_service(
    session: AsyncSession = Depends(get_session),
    results: ResultService = Depends(get_result_service),
    comfort: ComfortService = Depends(get_comfort_service),
) -> ComparisonService:
    """Provide the comparison service for a request."""
    return ComparisonService(session, results, comfort)
