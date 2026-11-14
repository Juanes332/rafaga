"""Atomic output directories under DATA_DIR."""

import pytest

from app.core.errors.solver_errors import InvalidPayloadError
from app.services.storage import output_dir_service as storage


def test_paths_cannot_escape_the_volume(tmp_path) -> None:
    with pytest.raises(InvalidPayloadError):
        storage.resolve(str(tmp_path), "../etc")


def test_publish_renames_tmp_atomically(tmp_path) -> None:
    final = storage.resolve(str(tmp_path), "results/a/b/c")
    tmp = storage.temp_dir(final)
    (tmp / "x").write_text("1")
    storage.publish(tmp, final)
    assert (final / "x").exists() and not tmp.exists()
    storage.discard(final)
    assert not final.exists()
