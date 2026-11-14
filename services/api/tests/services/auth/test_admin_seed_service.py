"""JOB-A01: the admin seed is insert-if-absent."""

from sqlalchemy import text

from app.configs.config import get_settings
from app.services.auth.admin_seed_service import seed_admin


async def test_seed_inserts_architect_when_absent(app, monkeypatch) -> None:  # noqa: ANN001
    """Both variables set and no such user inserts an architect."""
    monkeypatch.setenv("ADMIN_EMAIL", "Admin@Rafaga.test")
    monkeypatch.setenv("ADMIN_PASSWORD", "seed-password-1")
    get_settings.cache_clear()
    async with app.state.session_factory() as s:
        assert await seed_admin(s, get_settings()) is True
        row = (await s.execute(text("SELECT role, password_hash FROM users"))).one()
    assert row[0] == "architect" and row[1].startswith("$argon2id$")


async def test_seed_never_overwrites_existing_password(app, monkeypatch) -> None:  # noqa: ANN001
    """An existing user keeps their hash."""
    monkeypatch.setenv("ADMIN_EMAIL", "admin@rafaga.test")
    monkeypatch.setenv("ADMIN_PASSWORD", "seed-password-1")
    get_settings.cache_clear()
    async with app.state.session_factory() as s:
        await seed_admin(s, get_settings())
        before = (await s.execute(text("SELECT password_hash FROM users"))).scalar()
        monkeypatch.setenv("ADMIN_PASSWORD", "another-password-2")
        get_settings.cache_clear()
        assert await seed_admin(s, get_settings()) is False
        after = (await s.execute(text("SELECT password_hash FROM users"))).scalar()
    assert before == after


async def test_seed_skipped_when_a_variable_is_empty(app, monkeypatch) -> None:  # noqa: ANN001
    """Missing password means no seed."""
    monkeypatch.setenv("ADMIN_EMAIL", "admin@rafaga.test")
    get_settings.cache_clear()
    async with app.state.session_factory() as s:
        assert await seed_admin(s, get_settings()) is False
