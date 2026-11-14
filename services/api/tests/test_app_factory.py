"""create_app() builds independent, fully wired applications."""

from app.main import create_app


def test_factories_return_independent_apps() -> None:
    """Two calls share no state."""
    a, b = create_app(), create_app()
    assert a is not b
    assert a.state.rate_limiter is not b.state.rate_limiter
    assert a.state.engine is not b.state.engine
