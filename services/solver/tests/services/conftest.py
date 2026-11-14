"""Fixtures shared by service tests that need results on disk."""

import pytest

from tests.support.result_store import ResultStore, aggregate_payload, build_store


@pytest.fixture(scope="session")
def result_store(tmp_path_factory) -> ResultStore:
    """Return two real coarse results computed once per session."""
    return build_store(tmp_path_factory.mktemp("data"))


@pytest.fixture(scope="session")
def comfort_dir(result_store) -> str:
    """Return the directory of an aggregate computed from the store."""
    from app.services.comfort.aggregate_service import run_aggregate

    return run_aggregate(aggregate_payload(result_store), result_store.settings)["dir"]
