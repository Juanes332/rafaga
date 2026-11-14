"""Grids against the normative example of the job contract."""

import json
import math
from pathlib import Path

import pytest

from app.services.simulations import estimate_calculator as ec
from app.services.simulations import grid_service as g

EX = Path(__file__).resolve().parents[5] / "docs/architecture/contracts/examples"


def _scene() -> dict:
    return json.loads((EX / "scene.example.json").read_text())


def _job(name: str) -> dict:
    return json.loads((EX / name).read_text())


def test_wind_frame_axes_for_west_wind() -> None:
    """Wind from 270 deg advances towards +x with n = +y."""
    d, n = g.frame_axes(270.0)
    assert d == (1.0, 0.0) and n == (0.0, 1.0)


def test_sim_grid_2d_matches_plan2d_example() -> None:
    """The 2D sim grid equals the contract example byte for byte."""
    expected = _job("job.plan2d.example.json")["grid"]["sim"]
    assert g.sim_grid_wind(_scene(), 270.0, 1.0, volume=False) == expected


def test_sim_grid_3d_matches_volume_example() -> None:
    """The 3D sim grid equals the contract example."""
    expected = _job("job.volume3d.example.json")["grid"]["sim"]
    assert g.sim_grid_wind(_scene(), 270.0, 1.0, volume=True) == expected


def test_output_grid_matches_example_and_is_direction_free() -> None:
    """The output grid is the example and aligned to dx multiples."""
    assert g.output_grid_plan(_scene(), 1.0) == _job("job.plan2d.example.json")["grid"]["output"]
    aligned = g.output_grid_plan(_scene(), 3.0)
    assert aligned["origin_x"] % 3.0 == 0 and aligned["origin_y"] % 3.0 == 0


def test_blockage_above_three_percent_enlarges_the_domain() -> None:
    """A wide building triggers the Ly/Lz enlargement below 3 percent."""
    scene = _scene()
    scene["bounds"]["base_min"] = [-60.0, -15.0, 0.0]
    scene["bounds"]["base_max"] = [60.0, 15.0, 24.0]
    small = g.sim_grid_wind(scene, 0.0, 1.0, volume=True)
    # Wind from the north: lateral extent is x, 140 m wide with envelope.
    h = 24.0
    ly, lz = small["ny"], small["nz"]
    assert lz > 6 * h
    assert 140 * h / (ly * lz) < 0.03


def test_section_grids() -> None:
    """Section grids follow rule 4 and the wind comes from p1 to p0."""
    sim, out = g.section_grids(_scene(), [0.0, 0.0], [0.0, -100.0], 2.0)
    assert out == {"frame": "section", "s0": -120.0, "dx_m": 2.0, "ns": 290, "nz": 72}
    assert sim["wind_from_deg"] == pytest.approx(0.0)
    assert g.node_count(sim) == 290 * 72


def test_volume3d_top_is_five_building_heights() -> None:
    """The 3D box top is 5H (ceil(5H/dx) cells) while 2D sections keep 6H."""
    scene = _scene()  # H = 24 m
    scene["bounds"]["base_min"] = [-10.0, -5.0, 0.0]  # narrow: no blockage stretch
    scene["bounds"]["base_max"] = [10.0, 5.0, 24.0]
    vol = g.sim_grid_wind(scene, 270.0, 1.0, volume=True)
    assert vol["nz"] == math.ceil(5 * 24.0 / 1.0)
    vol_fine = g.sim_grid_wind(scene, 270.0, 0.7, volume=True)
    assert vol_fine["nz"] == math.ceil(round(5 * 24.0 / 0.7, 6))
    sec, _ = g.section_grids(scene, [0.0, 0.0], [0.0, -100.0], 1.0)
    assert sec["nz"] == 6 * 24


def test_blockage_stretch_raises_the_3d_top_above_five_h() -> None:
    """When blockage exceeds 3 percent the stretched top is above 5H."""
    scene = _scene()
    scene["bounds"]["base_min"] = [-60.0, -15.0, 0.0]
    scene["bounds"]["base_max"] = [60.0, 15.0, 24.0]
    grid = g.sim_grid_wind(scene, 0.0, 1.0, volume=True)
    assert grid["nz"] > math.ceil(5 * 24.0)
    assert 140 * 24.0 / (grid["ny"] * grid["nz"]) < 0.03


def test_25m_node_volume_estimate_fits_an_8gb_gpu() -> None:
    """A ~25 M-node 3D case stays under 7.2 GB and fits 8188 MiB of VRAM."""
    scene = _scene()
    dx = next(d / 100 for d in range(80, 140) if
              g.node_count(g.sim_grid_wind(scene, 270.0, d / 100, True)) <= 25_000_000)
    nodes = g.node_count(g.sim_grid_wind(scene, 270.0, dx, True))
    assert 22_000_000 <= nodes <= 25_000_000

    def build(x: float):  # noqa: ANN202
        return [(g.sim_grid_wind(scene, 270.0, x, True), g.output_grid_plan(scene, x))]

    node = {"online": True, "device": "gpu", "vram_total_bytes": 8188 * 2**20,
            "ram_budget_bytes": 10 * 2**30, "mlups_2d": 100.0, "mlups_3d": 800.0}
    est = ec.compute_estimate("volume3d", scene, dx, "auto", node, 3_000_000, build)
    assert est.memory_bytes <= 7.2e9 and est.fits
