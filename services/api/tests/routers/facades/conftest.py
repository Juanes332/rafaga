"""Fixtures for facade, alternative and scene router tests."""

from typing import Any

import pytest
from httpx import AsyncClient

from tests.support.scene_support import (
    BUILDING_ID,
    base_alternative_id,
    set_geometry,
    square_building,
)


@pytest.fixture
async def built(client: AsyncClient, architect, project, app) -> dict[str, Any]:  # noqa: ANN001
    """Return a project with one building and its base alternative id."""
    await set_geometry(app, project["id"], [square_building()])
    alt = await base_alternative_id(client, architect.headers, project["id"])
    return {"project_id": project["id"], "alt_id": alt, "building_id": BUILDING_ID}
