"""Settings endpoints."""

from httpx import AsyncClient


async def test_defaults_are_created_lazily(client: AsyncClient, architect, app) -> None:  # noqa: ANN001
    """First GET returns the documented defaults and stores the row."""
    from sqlalchemy import text

    r = await client.get("/api/v1/settings", headers=architect.headers)
    b = r.json()
    assert r.status_code == 200
    assert b["thresholds"] == {"k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1}
    assert b["turbulence_intensity_default"] == 0.25 and b["vegetation_cd"] == 0.2
    assert b["alternatives_limit"] == 8
    assert [c["threshold_ms"] for c in b["lawson"]["comfort"]] == [4, 6, 8, 10, None]
    assert [s["threshold_ms"] for s in b["lawson"]["safety"]] == [15, 20]
    assert b["lawson"]["exceedance_probability"] == 0.05
    async with app.state.session_factory() as s:
        n = (await s.execute(text("SELECT count(*) FROM user_settings"))).scalar()
    assert n == 1


async def test_patch_updates_and_persists(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """A valid patch is returned and visible to the next GET."""
    body = {"alternatives_limit": 12, "vegetation_cd": 0.3,
            "thresholds": {"k_accel": 1.5, "k_stagnation": 0.4, "dk_reduction": -0.2}}
    r = await client.patch("/api/v1/settings", headers=architect.headers, json=body)
    again = await client.get("/api/v1/settings", headers=architect.headers)
    assert r.status_code == 200 and r.json()["alternatives_limit"] == 12
    assert again.json()["thresholds"]["k_accel"] == 1.5 and again.json()["vegetation_cd"] == 0.3


async def test_patch_rejects_invalid_ranges(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """Each documented rule answers 422 validation_error."""
    bad_bodies = [
        {"thresholds": {"k_accel": 0.2, "k_stagnation": 0.3, "dk_reduction": -0.1}},
        {"alternatives_limit": 21},
        {"alternatives_limit": 0},
        {"lawson": {"exceedance_probability": 0.05, "safety_probability": 0.00025,
                    "comfort": [{"key": "a", "label_key": "a", "threshold_ms": 6},
                                {"key": "b", "label_key": "b", "threshold_ms": 4},
                                {"key": "c", "label_key": "c", "threshold_ms": None}],
                    "safety": [{"key": "s", "threshold_ms": 15}]}},
    ]
    for body in bad_bodies:
        r = await client.patch("/api/v1/settings", headers=architect.headers, json=body)
        assert (r.status_code, r.json()["code"]) == (422, "validation_error")


async def test_settings_are_per_user_and_need_auth(
    client: AsyncClient, architect, other_architect
) -> None:  # noqa: ANN001
    """One user's patch does not change another's; anonymous is 401."""
    await client.patch("/api/v1/settings", headers=architect.headers, json={"alternatives_limit": 3})
    other = await client.get("/api/v1/settings", headers=other_architect.headers)
    assert other.json()["alternatives_limit"] == 8
    assert (await client.get("/api/v1/settings")).status_code == 401
