"""Fixtures and builders for the geometry tests."""

import io
import uuid
from typing import Any

import ezdxf
import pytest
import trimesh


def building(
    footprint: list[list[float]] | None = None, height: float | None = 10.0, **extra: Any
) -> dict[str, Any]:
    """Return a Building payload on a synthetic local footprint."""
    return {
        "id": str(uuid.uuid4()),
        "footprint": footprint or [[0, 0], [10, 0], [10, 10], [0, 10]],
        "height_m": height,
        "source": "draw",
        **extra,
    }


def dxf_bytes(units: int = 6) -> bytes:
    """Return a DXF with two closed boxes, an open line and metadata."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = units
    msp = doc.modelspace()
    doc.layers.add("H12")
    doc.layers.add("plain")
    msp.add_lwpolyline([(100, 200), (110, 200), (110, 210), (100, 210)], close=True,
                       dxfattribs={"layer": "H12"})
    msp.add_lwpolyline([(120, 200), (130, 200), (130, 220), (120, 220)], close=True,
                       dxfattribs={"layer": "plain"})
    msp.add_lwpolyline([(0, 0), (5, 5), (9, 1)], close=False, dxfattribs={"layer": "plain"})
    out = io.StringIO()
    doc.write(out)
    return out.getvalue().encode()


def stepped_stl() -> bytes:
    """Return an STL of one 12 m tapering body (cone), which tiers every 3 m."""
    cone = trimesh.creation.cone(radius=5, height=12, sections=8)
    return cone.export(file_type="stl")


def two_box_obj() -> bytes:
    """Return an OBJ with two separate boxes of 20 m and 8 m height."""
    a = trimesh.creation.box(extents=[10, 10, 20])
    a.apply_translation([0, 0, 10])
    b = trimesh.creation.box(extents=[6, 6, 8])
    b.apply_translation([30, 0, 4])
    return trimesh.util.concatenate([a, b]).export(file_type="obj").encode()


@pytest.fixture
def geometry_url(project: dict[str, Any]) -> str:
    """Return the geometry URL of the default project."""
    return f"/api/v1/projects/{project['id']}/geometry"


def ifc_bytes() -> bytes:
    """Return a minimal IFC4 file: one IfcBuilding with a 10 x 0.3 x 12 wall."""
    import ifcopenshell
    import ifcopenshell.api
    import numpy as np

    api = ifcopenshell.api.run
    f = api("project.create_file", version="IFC4")
    proj = api("root.create_entity", f, ifc_class="IfcProject", name="p")
    api("unit.assign_unit", f)
    ctx = api("context.add_context", f, context_type="Model")
    body = api("context.add_context", f, context_type="Model", context_identifier="Body",
               target_view="MODEL_VIEW", parent=ctx)
    site = api("root.create_entity", f, ifc_class="IfcSite")
    bld = api("root.create_entity", f, ifc_class="IfcBuilding", name="Torre")
    api("aggregate.assign_object", f, products=[site], relating_object=proj)
    api("aggregate.assign_object", f, products=[bld], relating_object=site)
    wall = api("root.create_entity", f, ifc_class="IfcWall")
    rep = api("geometry.add_wall_representation", f, context=body, length=10, height=12,
              thickness=0.3)
    api("geometry.assign_representation", f, product=wall, representation=rep)
    api("spatial.assign_container", f, products=[wall], relating_structure=bld)
    api("geometry.edit_object_placement", f, product=wall, matrix=np.eye(4))
    return f.to_string().encode()
