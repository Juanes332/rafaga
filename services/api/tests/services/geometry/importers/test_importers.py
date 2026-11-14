"""Importer units: DXF, mesh and IFC readers."""

import pytest

from app.services.geometry.importers.dxf_importer import read_dxf
from app.services.geometry.importers.ifc_importer import read_ifc
from app.services.geometry.importers.importer_common import ImporterError
from app.services.geometry.importers.mesh_importer import read_mesh
from tests.routers.geometry.conftest import dxf_bytes, ifc_bytes, two_box_obj


def test_dxf_units_and_heights() -> None:
    """INSUNITS 6 is metres; layer H12 gives 12 m."""
    result = read_dxf(dxf_bytes(6))
    assert result.detected_unit == "m"
    assert sorted(b["height_m"] or 0 for b in result.buildings) == [0, 12.0]


def test_dxf_unknown_units() -> None:
    """INSUNITS 0 is unknown."""
    assert read_dxf(dxf_bytes(0)).detected_unit == "unknown"


def test_dxf_corrupt_raises_importer_error() -> None:
    """Garbage raises an error with a hint."""
    with pytest.raises(ImporterError) as caught:
        read_dxf(b"\x00\x01 garbage")
    assert caught.value.hint


def test_mesh_rejects_empty_and_garbage() -> None:
    """Unparseable meshes raise ImporterError."""
    with pytest.raises(ImporterError):
        read_mesh(b"nope", "stl", "x")


def test_mesh_obj_two_bodies() -> None:
    """Two separate boxes give two buildings."""
    assert len(read_mesh(two_box_obj(), "obj", "m").buildings) == 2


def test_ifc_box_and_metric_flag() -> None:
    """IFC output is already metric."""
    result = read_ifc(ifc_bytes())
    assert result.metric and len(result.buildings) == 1


def test_ifc_garbage_raises() -> None:
    """A non-IFC payload raises ImporterError."""
    with pytest.raises(ImporterError):
        read_ifc(b"not ifc")
