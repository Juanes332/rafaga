"""Seam to the scene domain, replaceable in tests."""

from typing import Any, Protocol
from uuid import UUID

from app.security.jwt.jwt_guard import CurrentUser


class SceneProvider(Protocol):
    """What the simulations domain needs from the scene domain."""

    async def compile_for_alternative(
        self, user: CurrentUser, alternative_id: UUID
    ) -> dict[str, Any]:
        """Return the canonical scene of an alternative."""


try:
    from app.services.scene.scene_service import get_scene_service
except ImportError:  # the scene batch has not landed yet

    def get_scene_service() -> SceneProvider:
        """Fail loudly when the scene service is absent."""
        raise RuntimeError("the scene service is not installed")
