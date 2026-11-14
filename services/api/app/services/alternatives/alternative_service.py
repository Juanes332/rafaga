"""Alternatives domain business logic."""

from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.alternative_errors import (
    AlternativeNotFoundError,
    AlternativesLimitError,
    BaseUndeletableError,
)
from app.models.alternatives.alternative_schemas import (
    AlternativeCreateRequest,
    AlternativePatchRequest,
    AlternativeResponse,
    summary_from_row,
)
from app.repositories.alternatives import alternative_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)


def _to_response(row) -> AlternativeResponse:  # noqa: ANN001
    """Build the response model from a list row."""
    return AlternativeResponse(
        id=row["id"], name=row["name"], is_base=row["is_base"], position=row["position"],
        element_count=row["element_count"], latest_results_summary=summary_from_row(row),
    )


class AlternativeService:
    """Create, rename, reorder and delete project alternatives."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService, settings: Settings) -> None:
        """Bind collaborators."""
        self._session = session
        self._access = access
        self._settings = settings

    async def _load(self, alt_id: UUID, user: CurrentUser, *, write: bool):  # noqa: ANN202
        """Return the alternative row after the ownership check."""
        row = await repo.find_alternative(self._session, alt_id)
        project_id = row["project_id"] if row else alt_id
        await self._access.resolve(project_id, user, write=write, not_found=AlternativeNotFoundError)
        return row

    async def _one(self, project_id: UUID, alt_id: UUID) -> AlternativeResponse:
        """Return one alternative as listed."""
        rows = await repo.list_alternatives(self._session, project_id)
        return _to_response(next(r for r in rows if r["id"] == alt_id))

    async def list(self, user: CurrentUser, project_id: UUID) -> list[AlternativeResponse]:
        """List a project's alternatives, base first."""
        await self._access.resolve(project_id, user)
        return [_to_response(r) for r in await repo.list_alternatives(self._session, project_id)]

    async def create(self, user: CurrentUser, project_id: UUID, body: AlternativeCreateRequest) -> AlternativeResponse:
        """Create a derived alternative copying another's elements."""
        await self._access.resolve(project_id, user, write=True)
        limit = await repo.alternatives_limit_for(self._session, user.id) or self._settings.alternatives_limit_default
        if await repo.count_derived(self._session, project_id) >= limit:
            raise AlternativesLimitError(details={"limit": limit})
        source = await self._source(project_id, body.from_alternative_id)
        row = await repo.insert_alternative(self._session, project_id, body.name)
        await repo.copy_elements(self._session, source, row["id"])
        await self._session.commit()
        return await self._one(project_id, row["id"])

    async def _source(self, project_id: UUID, from_id: UUID | None) -> UUID:
        """Return the alternative to copy from; default is the base."""
        rows = await repo.list_alternatives(self._session, project_id)
        wanted = [r for r in rows if r["id"] == from_id] if from_id else [r for r in rows if r["is_base"]]
        if not wanted:
            raise AlternativeNotFoundError()
        return wanted[0]["id"]

    async def patch(self, user: CurrentUser, alt_id: UUID, body: AlternativePatchRequest) -> AlternativeResponse:
        """Rename and/or move an alternative."""
        row = await self._load(alt_id, user, write=True)
        if body.name is not None:
            await repo.rename_alternative(self._session, alt_id, body.name)
        if body.position is not None and not row["is_base"]:
            await self._move(row["project_id"], alt_id, body.position)
        await self._session.commit()
        return await self._one(row["project_id"], alt_id)

    async def _move(self, project_id: UUID, alt_id: UUID, position: int) -> None:
        """Move a derived alternative; the base always holds position 0."""
        ids = await repo.derived_ids_in_order(self._session, project_id)
        ids.remove(alt_id)
        ids.insert(max(0, min(position - 1, len(ids))), alt_id)
        await repo.set_positions(self._session, ids)

    async def delete(self, user: CurrentUser, alt_id: UUID) -> None:
        """Delete a non-base alternative with its elements and results."""
        row = await self._load(alt_id, user, write=True)
        if row["is_base"]:
            raise BaseUndeletableError()
        await repo.delete_alternative(self._session, alt_id)
        await self._session.commit()


def get_alternative_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: Settings = Depends(get_settings),
) -> AlternativeService:
    """Provide the alternative service for a request."""
    return AlternativeService(session, access, settings)
