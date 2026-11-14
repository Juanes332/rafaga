"""Shared fixtures for the whole suite.

Every pytest session creates its own throwaway database on a Postgres
server (``TEST_DATABASE_URL`` pointing at a server, or a postgres:16
container started on a kernel-assigned port) and migrates it with
Alembic, so parallel sessions never collide.
"""

import os
import subprocess
import sys
import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient

TEST_JWT_SECRET = "test-jwt-secret-0123456789-abcdefghij"
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://x:x@127.0.0.1:1/x")
os.environ.setdefault("JWT_SECRET", TEST_JWT_SECRET)

_CONTAINER = "rafaga-api-pytest-"


def _server_url() -> tuple[str, str | None]:
    """Return an admin URL for a Postgres server and a container to stop."""
    if os.environ.get("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"], None
    name = _CONTAINER + uuid.uuid4().hex[:8]
    subprocess.run(
        ["docker", "run", "-d", "--rm", "--name", name, "-p", "0:5432",
         "-e", "POSTGRES_PASSWORD=test", "postgres:16-alpine"],
        check=True, capture_output=True,
    )
    port = subprocess.run(
        ["docker", "port", name, "5432/tcp"], check=True, capture_output=True, text=True
    ).stdout.split(":")[-1].split()[0]
    url = f"postgresql+psycopg://postgres:test@127.0.0.1:{port}/postgres"
    engine = sa.create_engine(url)
    for _ in range(60):
        try:
            engine.connect().close()
            break
        except sa.exc.OperationalError:
            subprocess.run(["sleep", "0.5"])
    return url, name


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """Create a private migrated database and drop it afterwards."""
    server, container = _server_url()
    name = "t_" + uuid.uuid4().hex[:12]
    admin = sa.create_engine(server, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(sa.text(f'CREATE DATABASE "{name}"'))
    url = server.rsplit("/", 1)[0] + "/" + name
    os.environ["DATABASE_URL"] = url
    os.environ["JWT_SECRET"] = TEST_JWT_SECRET
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=os.environ.copy(),
                   capture_output=True)
    yield url
    with admin.connect() as conn:
        conn.execute(sa.text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()
    if container:
        subprocess.run(["docker", "stop", container], capture_output=True)


@pytest.fixture(autouse=True)
def _environment(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> Iterator[None]:
    """Provide deterministic settings and clear the cache per test."""
    from app.configs.config import get_settings

    if "database_url" in request.fixturenames or "client" in request.fixturenames:
        monkeypatch.setenv("DATABASE_URL", request.getfixturevalue("database_url"))
    monkeypatch.setenv("JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RATE_LIMIT_ANON_PER_MINUTE", "100000")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "100000")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_PER_MINUTE", "100000")
    monkeypatch.setenv("RATE_LIMIT_TILES_PER_MINUTE", "100000")
    monkeypatch.setenv("TRUST_PROXY", "false")
    monkeypatch.setenv("ADMIN_EMAIL", "")
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _clean_database(request: pytest.FixtureRequest) -> Iterator[None]:
    """Empty every table after each test that touched the database."""
    yield
    if "database_url" in request.fixturenames or "client" in request.fixturenames:
        engine = sa.create_engine(request.getfixturevalue("database_url"))
        with engine.begin() as conn:
            conn.execute(sa.text(
                "TRUNCATE users, external_cache, solver_nodes RESTART IDENTITY CASCADE"))
        engine.dispose()


@pytest.fixture
async def app(database_url: str) -> AsyncIterator[Any]:
    """Return a freshly built application bound to the test database."""
    from app.main import create_app

    application = create_app()
    yield application
    await application.state.engine.dispose()


@pytest.fixture
async def client(app: Any) -> AsyncIterator[AsyncClient]:
    """Return an in-process HTTP client bound to the app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class Actor:
    """A seeded user with ready-made auth headers."""

    def __init__(self, user_id: str, email: str, role: str, headers: dict[str, str]) -> None:
        """Hold identity and headers."""
        self.id, self.email, self.role, self.headers = user_id, email, role, headers


@pytest.fixture
def make_actor(client: AsyncClient, app: Any):  # noqa: ANN201
    """Return a factory creating a user directly in the database."""
    from app.security.jwt.token_codec import issue_token
    from app.configs.config import get_settings
    from app.repositories.users import user_repository as repo
    from app.security.password.password_hasher import hash_password

    async def factory(role: str = "architect", email: str | None = None) -> Actor:
        email = email or f"{role}-{uuid.uuid4().hex[:6]}@rafaga.test"
        async with app.state.session_factory() as session:
            row = await repo.insert_user(session, email, hash_password("password-12345"), role)
            await session.commit()
        token, _ = issue_token(get_settings(), str(row["id"]), role)
        return Actor(str(row["id"]), email, role, {"Authorization": f"Bearer {token}"})

    return factory


@pytest.fixture
async def architect(make_actor) -> Actor:  # noqa: ANN001
    """Return a seeded architect."""
    return await make_actor("architect")


@pytest.fixture
async def other_architect(make_actor) -> Actor:  # noqa: ANN001
    """Return a different architect, for ownership tests."""
    return await make_actor("architect")


@pytest.fixture
async def reviewer(make_actor) -> Actor:  # noqa: ANN001
    """Return a seeded reviewer."""
    return await make_actor("reviewer")


@pytest.fixture
async def project(client: AsyncClient, architect: Actor) -> dict[str, Any]:
    """Create a project owned by the architect through the API."""
    r = await client.post("/api/v1/projects", headers=architect.headers, json={"name": "P"})
    assert r.status_code == 201
    return r.json()
