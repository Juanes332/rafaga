"""Facades domain business logic: strategies and elements."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.alternative_errors import (
    AlternativeNotFoundError,
    BaseLockedError,
    EdgeNotFoundError,
    ElementNotFoundError,
    NoBuildingsError,
)
from app.models.facades.facade_schemas import (
    FacadeElementCreateRequest,
    FacadeElementResponse,
    FacadeElementWithAdjustments,
    FacadeStrategyResponse,
)
from app.repositories.alternatives.alternative_repository import find_alternative
from app.repositories.facades import facade_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.facades.facade_strategies_catalogue import STRATEGIES, clamp_params
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)


def list_strategies() -> list[FacadeStrategyResponse]:
    """Return the catalogue as response models."""
    return [
        FacadeStrategyResponse(type=t, label_key=f"facade.{t}.label",
                               help_key=f"facade.{t}.help", parameters=specs)
        for t, specs in STRATEGIES.items()
    ]


def is_orphaned(buildings: list[dict[str, Any]], building_id: Any, edge_index: int) -> bool:
    """Return whether the building or its edge no longer exists."""
    match = next((b for b in buildings if str(b["id"]) == str(building_id)), None)
    return match is None or edge_index >= len(match["footprint"])


class FacadeService:
    """Create, read, update and delete facade elements."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService) -> None:
        """Bind collaborators."""
        self._session = session
        self._access = access

    def _view(self, row: Mapping[str, Any], buildings: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the element dict including the orphaned flag."""
        return {
            "id": row["id"], "building_id": row["building_id"], "edge_index": row["edge_index"],
            "type": row["type"], "params": row["params"],
            "orphaned": is_orphaned(buildings, row["building_id"], row["edge_index"]),
        }

    async def _lock_check(self, project_id: UUID, is_base: bool, confirmed: bool) -> None:
        """Refuse base edits while alternatives exist, unless confirmed."""
        if is_base and not confirmed and await repo.has_derived(self._session, project_id):
            raise BaseLockedError()

    async def _alternative(self, alt_id: UUID, user: CurrentUser, *, write: bool):  # noqa: ANN202
        """Return the alternative row after the ownership check."""
        row = await find_alternative(self._session, alt_id)
        await self._access.resolve(row["project_id"] if row else alt_id, user, write=write,
                                   not_found=AlternativeNotFoundError)
        return row

    async def _element(self, element_id: UUID, user: CurrentUser, *, write: bool):  # noqa: ANN202
        """Return the element row after the ownership check."""
        row = await repo.find_element(self._session, element_id)
        await self._access.resolve(row["project_id"] if row else element_id, user, write=write,
                                   not_found=ElementNotFoundError)
        return row

    async def list(self, user: CurrentUser, alt_id: UUID) -> list[FacadeElementResponse]:
        """List an alternative's elements with orphan flags."""
        alt = await self._alternative(alt_id, user, write=False)
        buildings = await repo.project_buildings(self._session, alt["project_id"])
        rows = await repo.list_elements(self._session, alt_id)
        return [FacadeElementResponse(**self._view(r, buildings)) for r in rows]

    async def create(self, user: CurrentUser, alt_id: UUID, body: FacadeElementCreateRequest, confirm: bool) -> FacadeElementWithAdjustments:
        """Create an element, clamping params into range."""
        alt = await self._alternative(alt_id, user, write=True)
        params, adjustments = clamp_params(body.type, body.params)
        buildings = await repo.project_buildings(self._session, alt["project_id"])
        if not buildings:
            raise NoBuildingsError()
        if is_orphaned(buildings, body.building_id, body.edge_index):
            raise EdgeNotFoundError()
        await self._lock_check(alt["project_id"], alt["is_base"], confirm)
        row = await repo.insert_element(self._session, alt_id, body.building_id, body.edge_index, body.type, params)
        await self._session.commit()
        return FacadeElementWithAdjustments(**self._view(row, buildings), adjustments=adjustments)

    async def patch(self, user: CurrentUser, element_id: UUID, new: dict[str, Any], confirm: bool) -> FacadeElementWithAdjustments:
        """Merge new params into an element and clamp the result."""
        row = await self._element(element_id, user, write=True)
        await self._lock_check(row["project_id"], row["is_base"], confirm)
        params, adjustments = clamp_params(row["type"], {**row["params"], **new})
        adjustments = [a for a in adjustments if a["field"] in new]
        await repo.update_params(self._session, element_id, params)
        await self._session.commit()
        buildings = await repo.project_buildings(self._session, row["project_id"])
        return FacadeElementWithAdjustments(
            **self._view({**row, "params": params}, buildings), adjustments=adjustments)

    async def delete(self, user: CurrentUser, element_id: UUID, confirm: bool) -> None:
        """Delete an element."""
        row = await self._element(element_id, user, write=True)
        await self._lock_check(row["project_id"], row["is_base"], confirm)
        await repo.delete_element(self._session, element_id)
        await self._session.commit()


def get_facade_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
) -> FacadeService:
    """Provide the facade service for a request."""
    return FacadeService(session, access)
