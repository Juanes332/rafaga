"""Injectable HTTP client seam for every outbound call."""

from collections.abc import AsyncIterator

import httpx
from fastapi import Depends

from app.configs.config import Settings, get_settings


async def get_http_client(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[httpx.AsyncClient]:
    """Yield a client; tests mock it with respx or override this."""
    async with httpx.AsyncClient(
        timeout=settings.external_timeout_s, follow_redirects=True
    ) as client:
        yield client
