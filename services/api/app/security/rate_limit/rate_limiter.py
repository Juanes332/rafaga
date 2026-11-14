"""Two-tier rate limiting: client address first, principal second."""

import ipaddress
import math
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from limits import RateLimitItemPerMinute
from limits.storage import storage_from_string
from limits.strategies import FixedWindowRateLimiter
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.configs.config import get_settings
from app.core.errors.rate_limit_errors import RateLimitedError

# The container HEALTHCHECK must never be throttled by either tier.
EXEMPT_PATHS = frozenset({"/health"})

ADDRESS_TIER = "anon"
PRINCIPAL_TIER = "principal"
LOGIN_TIER = "login"
TILES_TIER = "tiles"
TILES_ADDRESS_TIER = "tiles-addr"
TILES_PREFIX = "/api/v1/tiles/"


class RateLimiter:
    """Count hits per tier and key against a pluggable storage.

    `memory://` counts per process, so N replicas grant N times the
    budget. Point `RATE_LIMIT_STORAGE_URI` at a shared store (for
    example `redis://redis:6379`, with the `limits[redis]` extra
    installed) the moment there is more than one replica.
    """

    def __init__(self, storage_uri: str) -> None:
        """Open the storage the counters live in."""
        self._strategy = FixedWindowRateLimiter(storage_from_string(storage_uri))

    def hit(self, tier: str, key: str, per_minute: int) -> int | None:
        """Count one request; return seconds to wait when over budget."""
        # The tier is the namespace, so tiers never share a counter.
        item = RateLimitItemPerMinute(per_minute, namespace=tier)
        if self._strategy.hit(item, key):
            return None
        reset = self._strategy.get_window_stats(item, key).reset_time
        return max(1, math.ceil(reset - time.time()))


def _fold_address(host: str) -> str:
    """Collapse an IPv6 address to its /64; IPv4 passes unchanged.

    One host is routinely handed a whole IPv6 /64, so a per-address
    bucket would give it 2**64 budgets. An IPv4-mapped IPv6 address
    is unwrapped to the IPv4 address it carries.
    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host
    if isinstance(address, ipaddress.IPv4Address):
        return str(address)
    if address.ipv4_mapped is not None:
        return str(address.ipv4_mapped)
    return str(ipaddress.IPv6Network((int(address), 64), strict=False))


def client_address_key(request: Request, trust_proxy: bool) -> str:
    """Key tier 1 by the client address, never by a credential header.

    Authorization and X-API-Key are chosen by the caller, so keying
    on them lets one address mint a fresh budget per request.
    X-Forwarded-For is honoured only behind a proxy we operate, and
    only its right-most entry: that is the hop our own proxy added.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if trust_proxy and forwarded:
        host = forwarded.split(",")[-1].strip()
    else:
        host = request.client.host if request.client else "unknown"
    return f"addr:{_fold_address(host)}"


def principal_key(request: Request) -> str:
    """Key tier 2 by the principal an auth guard published.

    Raises LookupError when no guard ran: tier 2 must sit after
    authentication, and a silent fallback would hide a wiring bug.
    """
    principal = getattr(request.state, "principal", None)
    if principal is None:
        raise LookupError("No authenticated principal on this request.")
    return str(principal)


def _limiter_of(request: Request) -> RateLimiter:
    """Return the limiter the application owns."""
    return request.app.state.rate_limiter


def register_rate_limiting(app: FastAPI) -> None:
    """Install tier 1 as middleware; tier 2 is a router dependency."""
    app.state.rate_limiter = RateLimiter(get_settings().rate_limit_storage_uri)

    @app.middleware("http")
    async def address_rate_limit(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Spend the caller's address budget before authentication runs."""
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        settings = get_settings()
        key = client_address_key(request, settings.trust_proxy)
        # MapLibre bursts dozens of tiles per pan (ADR-26): they spend
        # their own address bucket instead of the general one.
        is_tile = request.url.path.startswith(TILES_PREFIX)
        tier = TILES_ADDRESS_TIER if is_tile else ADDRESS_TIER
        budget = (
            settings.rate_limit_tiles_per_minute
            if is_tile
            else settings.rate_limit_anon_per_minute
        )
        wait = _limiter_of(request).hit(tier, key, budget)
        if wait is None:
            return await call_next(request)
        error = RateLimitedError(retry_after=wait)
        return JSONResponse(
            status_code=error.status_code,
            content=error.as_body(),
            headers=error.headers,
        )


async def enforce_principal_rate_limit(request: Request) -> None:
    """Spend the authenticated principal's budget (tier 2).

    List it AFTER the auth guard in the router's `dependencies`.
    """
    wait = _limiter_of(request).hit(
        PRINCIPAL_TIER,
        principal_key(request),
        get_settings().rate_limit_per_minute,
    )
    if wait is not None:
        raise RateLimitedError(retry_after=wait)


async def enforce_tiles_rate_limit(request: Request) -> None:
    """Spend the principal's tile budget (tier 2, tiles router only)."""
    wait = _limiter_of(request).hit(
        TILES_TIER,
        principal_key(request),
        get_settings().rate_limit_tiles_per_minute,
    )
    if wait is not None:
        raise RateLimitedError(retry_after=wait)


async def enforce_login_rate_limit(request: Request) -> None:
    """Spend the brute-force budget of /auth/login and /auth/setup."""
    settings = get_settings()
    key = client_address_key(request, settings.trust_proxy)
    wait = _limiter_of(request).hit(
        LOGIN_TIER, key, settings.rate_limit_login_per_minute
    )
    if wait is not None:
        raise RateLimitedError(retry_after=wait)
