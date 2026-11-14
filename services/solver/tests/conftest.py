"""Global fixtures and markers for the solver suite."""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("WORKER_ENABLED", "false")
CONTRACTS = ROOT.parents[1] / "docs" / "architecture" / "contracts"


@pytest.fixture(autouse=True)
def _settings_isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Give every test fresh settings and a throwaway data directory."""
    from app.configs.config import get_settings

    monkeypatch.setenv("WORKER_ENABLED", "false")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def all_route_paths(app) -> set[str]:
    """Return every registered path, including routes of included routers."""
    paths: set[str] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if path is not None:
            paths.add(path)
            continue
        inner = getattr(route, "original_router", None)
        if inner is not None:
            paths.update(p for p in (getattr(r, "path", None) for r in inner.routes) if p)
    return paths


@pytest.fixture(scope="session")
def pg_url():
    """Start one disposable Postgres for the integration session."""
    from tests.support import postgres_container

    container, url = postgres_container.start()
    yield url
    postgres_container.stop(container)


@pytest.fixture
def db_url(pg_url):
    """Return the session database emptied for this test."""
    from tests.support.postgres_container import reset

    reset(pg_url)
    return pg_url
