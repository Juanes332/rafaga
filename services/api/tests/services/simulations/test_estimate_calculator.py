"""Estimate, budget and coarsening rules of ADR-10."""

import json
from pathlib import Path

from app.services.simulations import estimate_calculator as ec
from app.services.simulations import grid_service as g
from app.services.simulations import simulation_constants as c

EX = Path(__file__).resolve().parents[5] / "docs/architecture/contracts/examples"
SCENE = json.loads((EX / "scene.example.json").read_text())


def _node(**kw) -> dict:  # noqa: ANN003
    base = {"online": True, "device": "cpu", "vram_total_bytes": None,
            "ram_budget_bytes": 10 * 2**30, "mlups_2d": 100.0, "mlups_3d": 50.0}
    return {**base, **kw}


def _build(kind: str):  # noqa: ANN202
    def build(dx: float):  # noqa: ANN202
        vol = kind == "volume3d"
        return [(g.sim_grid_wind(SCENE, 270.0, dx, vol), g.output_grid_plan(SCENE, dx))]
    return build


def test_2d_memory_equals_contract_example() -> None:
    """Memory is nodes*104 + 512 MiB, as in job.plan2d.example.json."""
    est = ec.compute_estimate("plan2d", SCENE, 1.0, "auto", _node(), 3_000_000, _build("plan2d"))
    assert est.memory_bytes == 552554112 and est.fits and est.proposed_dx_m is None
    assert est.eta_seconds > 0


def test_offline_solver_never_fits_and_invents_nothing() -> None:
    """No solver means budget 0 and a solver_offline reason."""
    est = ec.compute_estimate("plan2d", SCENE, 1.0, "auto", None, 3_000_000, _build("plan2d"))
    assert (est.fits, est.budget_bytes, est.rejected_reason) == (False, 0, "solver_offline")


def test_gpu_budget_uses_85_percent_of_vram_minus_overhead() -> None:
    """Budget = 0.85*VRAM - 512 MiB on GPU."""
    node = _node(device="gpu", vram_total_bytes=8 * 2**30)
    est = ec.compute_estimate("volume3d", SCENE, 1.0, "auto", node, 3_000_000, _build("volume3d"))
    assert est.budget_bytes == int(0.85 * 8 * 2**30 - 512 * 2**20) and est.device == "gpu"


def test_forced_gpu_without_gpu_is_unavailable() -> None:
    """Asking for a GPU on a CPU solver is rejected."""
    est = ec.compute_estimate("plan2d", SCENE, 1.0, "gpu", _node(), 3_000_000, _build("plan2d"))
    assert est.rejected_reason == "device_unavailable" and not est.fits


def test_cpu_3d_is_capped_by_node_limit_and_coarsened_to_quarter_metres() -> None:
    """3D on CPU is capped; the proposal is a 0.25 m multiple that fits."""
    est = ec.compute_estimate("volume3d", SCENE, 0.5, "cpu", _node(), 3_000_000, _build("volume3d"))
    assert not est.fits and est.proposed_dx_m is not None
    assert est.proposed_dx_m % 0.25 == 0 and est.proposed_dx_m > 0.5
    again = ec.compute_estimate(
        "volume3d", SCENE, est.proposed_dx_m, "cpu", _node(), 3_000_000, _build("volume3d"))
    assert again.fits and again.nodes <= 3_000_000


def test_buildings_narrower_than_four_cells_are_rejected() -> None:
    """A 20 m wide building at dx 6 is under 4 cells."""
    est = ec.compute_estimate("plan2d", SCENE, 6.0, "auto", _node(), 3_000_000, _build("plan2d"))
    assert est.rejected_reason == "buildings_too_small" and not est.fits


def test_buildings_too_small_proposes_the_coarsest_valid_dx() -> None:
    """The proposal is the coarsest 0.25 m multiple that keeps 4 cells per building."""
    for kind in ("plan2d", "volume3d"):
        node = _node(device="gpu", vram_total_bytes=8 * 2**30)
        est = ec.compute_estimate(kind, SCENE, 6.0, "auto", node, 3_000_000, _build(kind))
        width = ec.smallest_building_width(SCENE)
        assert est.rejected_reason == "buildings_too_small" and not est.fits
        p = est.proposed_dx_m
        assert p is not None and p % 0.25 == 0
        assert width / p >= 4 and width / (p + 0.25) < 4
        again = ec.compute_estimate(kind, SCENE, p, "auto", node, 3_000_000, _build(kind))
        assert again.fits and again.rejected_reason is None


def test_no_proposal_when_no_dx_satisfies_memory_and_building_rule() -> None:
    """If the finest legal dx exceeds the budget there is nothing to propose."""
    at6 = ec.compute_estimate("plan2d", SCENE, 6.0, "cpu", _node(), 3_000_000, _build("plan2d"))
    node = _node(ram_budget_bytes=at6.memory_bytes)
    est = ec.compute_estimate("plan2d", SCENE, 6.0, "cpu", node, 3_000_000, _build("plan2d"))
    assert est.rejected_reason == "buildings_too_small" and est.proposed_dx_m is None


def test_time_model_matches_measured_runs_within_15_percent() -> None:
    """RTX 4060: 3D 2.74 M nodes took 81 s and 2D took ~4.3 s (rounded up, never optimistic)."""
    node = _node(device="gpu", mlups_2d=3386.0, mlups_3d=947.0)
    sim3 = {"frame": "wind", "nx": 227, "ny": 110, "nz": 110, "dx_m": 2.0}
    assert abs(ec.model_seconds("volume3d", [sim3], node) - 81) <= 12
    sim2 = {"frame": "wind", "nx": 700, "ny": 500, "nz": None, "dx_m": 1.0}
    assert 3 <= ec.model_seconds("plan2d", [sim2], node) <= 5.5


def test_time_model_is_slower_per_node_on_small_grids_and_has_fixed_overhead() -> None:
    """Small grids run below peak MLUPS and every job pays the fixed start-up cost."""
    node = _node(device="gpu", mlups_3d=900.0)
    small = {"frame": "wind", "nx": 100, "ny": 10, "nz": 10, "dx_m": 2.0}
    big = {"frame": "wind", "nx": 100, "ny": 100, "nz": 100, "dx_m": 2.0}
    t_small = ec.model_seconds("volume3d", [small], node)
    t_big = ec.model_seconds("volume3d", [big], node)
    assert t_small >= c.FIXED_OVERHEAD_S["volume3d"]
    per_update_small = (t_small - c.FIXED_OVERHEAD_S["volume3d"]) / (100 * 100_000)
    per_update_big = (t_big - c.FIXED_OVERHEAD_S["volume3d"]) / (100 * 1_000_000)
    assert per_update_small > per_update_big


def test_null_mlups_falls_back_to_the_adr16_constant() -> None:
    """A node without measured MLUPS still yields an ETA from ADR-16."""
    node = _node(mlups_2d=None, mlups_3d=None)
    for kind in ("plan2d", "volume3d"):
        est = ec.compute_estimate(kind, SCENE, 1.0, "cpu", node, 3_000_000, _build(kind))
        assert est.eta_seconds > 0, kind
    assert c.CPU_FALLBACK_MLUPS["volume3d"] > 0 and c.CPU_FALLBACK_MLUPS["plan2d"] > 0
