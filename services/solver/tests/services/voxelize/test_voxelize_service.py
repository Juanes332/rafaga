"""Voxelizer tests: properties on the contract scene plus golden files."""

from pathlib import Path

import numpy as np
import pytest

from app.models.scene.scene_schemas import Scene
from app.services.lattice.lattice_problem import POROUS, SOLID
from app.services.voxelize.coverage_service import AxisGrid
from app.services.voxelize.frame_transform import WindFrame
from app.services.voxelize.voxelize_section import SectionSpec, voxelize_section
from app.services.voxelize.voxelize_service import PlanSpec, voxelize_plan
from tests.support.contracts import example

GOLDEN = Path(__file__).resolve().parents[2] / "fixtures" / "voxelize"


@pytest.fixture
def scene() -> Scene:
    return Scene.model_validate(example("scene.example"))


def _output_plan(scene: Scene) -> np.ndarray:
    grid = AxisGrid(-68.0, -73.0, 1.0, 136, 146)
    return voxelize_plan(scene, PlanSpec(grid, WindFrame.identity()))


def test_plan_building_is_solid_with_exact_area(scene) -> None:
    vox = _output_plan(scene)
    assert (vox.mask == SOLID).sum() == 20 * 30


def test_plan_thin_fins_screen_and_vegetation_become_porous(scene) -> None:
    vox = _output_plan(scene)
    # Cell column x in [-11, -10) holds the 0.5 m fins and is porous, not solid.
    fins = vox.mask[73 - 1 + 10, 68 - 11]
    assert fins == POROUS
    screen_row = vox.mask[73 - 16, 68 - 10 : 68 + 10]
    assert (screen_row == POROUS).all()
    veg = vox.mask[73 - 15 : 73 + 15, 68 + 11 : 68 + 14]
    assert (veg == POROUS).all()
    assert vox.ptable[vox.pid[73, 68 + 12], 4] == pytest.approx(0.2)


def test_canopy_above_analysis_height_is_ignored_in_plan(scene) -> None:
    vox = _output_plan(scene)
    assert (vox.mask[73 + 15 : 73 + 17, 68 - 10 : 68 + 10] == 0).all()


def test_rotated_sim_grid_keeps_building_area(scene) -> None:
    grid = AxisGrid(-140.0, -145.0, 1.0, 520, 290)
    vox = voxelize_plan(scene, PlanSpec(grid, WindFrame.from_wind(225.0)))
    assert abs(int((vox.mask == SOLID).sum()) - 600) < 30


def test_volume_has_canopy_as_horizontal_porous_plate(scene) -> None:
    grid = AxisGrid(-30.0, -30.0, 1.0, 60, 60)
    vox = voxelize_plan(scene, PlanSpec(grid, WindFrame.identity(), z_levels=30))
    assert (vox.mask[:24, 15:45, 20:40] == SOLID).all()
    plate = vox.pid[3, 30 + 16, 30]
    assert vox.mask[3, 46, 30] == POROUS and vox.ptable[plate, 3] == 1.0


def test_section_cuts_building_and_ground_row(scene) -> None:
    spec = SectionSpec((-60.0, 0.0), (60.0, 0.0), -10.0, 1.0, 140, 40)
    vox = voxelize_section(scene, spec)
    solid_cols = np.flatnonzero((vox.mask[0] == SOLID))
    # Cell 59 holds the 0.5 m-deep fin cut lengthwise (coverage 0.5 -> wall).
    assert solid_cols.min() == 59 and solid_cols.max() == 79
    assert (vox.mask[:24, 70] == SOLID).all() and vox.mask[24, 70] == 0


@pytest.mark.parametrize("name,builder", [
    ("plan_output", lambda s: _output_plan(s)),
    ("plan_sim_270", lambda s: voxelize_plan(s, PlanSpec(AxisGrid(-140.0, -145.0, 1.0, 520, 290), WindFrame.from_wind(270.0)))),
    ("volume_coarse", lambda s: voxelize_plan(s, PlanSpec(AxisGrid(-40.0, -40.0, 2.0, 40, 40), WindFrame.from_wind(200.0), z_levels=16))),
])
def test_golden_files(scene, name, builder) -> None:
    vox = builder(scene)
    path = GOLDEN / f"{name}.npz"
    if not path.exists():  # First run writes the reviewed golden file.
        np.savez_compressed(path, mask=vox.mask, pid=vox.pid, ptable=vox.ptable)
    gold = np.load(path)
    assert np.array_equal(gold["mask"], vox.mask)
    assert np.array_equal(gold["pid"], vox.pid)
    assert np.allclose(gold["ptable"], vox.ptable)


def test_thin_solid_plates_block_their_normal_flow_whatever_the_cell_size() -> None:
    from app.services.porous.porous_model import idelchik_zeta
    from tests.support.scenario_factory import SceneBuilder

    b = SceneBuilder().block("A", 0, 0, 20, 20, 20)
    b.canopy("c", -3, 0, 0, 20, 4.0)  # 0.3 m slab in a 2 m layer
    b.fin("f", 4, 20, 4.15, 23, 20)  # 0.15 m fin, 2 m cells
    sc = Scene.model_validate(b.build())
    grid = AxisGrid(-10.0, -10.0, 2.0, 20, 20)
    vox = voxelize_plan(sc, PlanSpec(grid, WindFrame.identity(), z_levels=12))
    near_solid = 0.5 * float(idelchik_zeta(0.05))
    canopy = vox.ptable[vox.pid[2, 7, 4]]  # z 4..6, y 4..6, x -2..0
    fin = vox.ptable[vox.pid[5, 15, 7]]  # z 10..12, y 20..22, x 4..6
    assert canopy[0] >= 0.9 * near_solid and canopy[3] == 1.0
    assert fin[0] >= 0.9 * near_solid and abs(fin[1]) == 1.0


@pytest.mark.parametrize("dx,offset", [(2.0, 0.0), (2.0, 0.5), (2.0, 1.0), (2.0, 4.0),
                                       (2.5, 0.5), (1.0, 0.5)])
def test_facade_screen_keeps_its_full_resistance_next_to_the_wall(dx, offset) -> None:
    """A celosia 0.5 m off a facade must not lose its drag inside the wall cells.

    The band is widened to one cell; centred on the screen it reached into
    the building, whose solid cells dropped up to half of zeta.
    """
    from app.services.porous.porous_model import idelchik_zeta
    from tests.support.scenario_factory import SceneBuilder

    b = SceneBuilder().block("T", 0, 0, 16, 24, 18)
    b.screen("s", -offset - 0.1, 0, -offset, 24, 3.0, (-1.0, 0.0))
    grid = AxisGrid(-20.0, -10.0, dx, int(56 / dx), int(44 / dx))
    vox = voxelize_plan(Scene.model_validate(b.build()), PlanSpec(grid, WindFrame.identity(), z_levels=4))
    a = np.where(vox.mask == POROUS, vox.ptable[vox.pid, 0], 0.0)
    row = int((12.0 + 10.0) // dx)
    integral = a[0, row, : int(20.0 // dx)].sum()  # cells upwind of the facade
    assert integral == pytest.approx(0.5 * float(idelchik_zeta(0.4)), rel=0.1)


def test_screen_without_normal_uses_its_thin_axis() -> None:
    from tests.support.scenario_factory import SceneBuilder

    b = SceneBuilder().block("T", 0, 0, 16, 24, 18)
    b.screen("s", -4.1, 0, -4.0, 24, 3.0, (-1.0, 0.0))
    raw = b.build()
    raw["porous"][0]["normal"] = None
    grid = AxisGrid(-20.0, -10.0, 2.0, 28, 22)
    vox = voxelize_plan(Scene.model_validate(raw), PlanSpec(grid, WindFrame.identity(), z_levels=4))
    rows = vox.ptable[np.unique(vox.pid[vox.mask == POROUS])]
    assert np.allclose(np.abs(rows[:, 1]), 1.0)
