"""Peak VRAM of a ~25 M-node volume3d case stays within the ADR-10 budget (BL-02)."""

import math

import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.bench.bench_memory import PeakMemory
from app.services.lbm3d.lbm3d_case import build_volume_case
from tests.support.gpu_marks import requires_gpu
from tests.support.payload_factory import plan_payload
from tests.support.stepper_choice import fastest

pytestmark = [pytest.mark.slow, pytest.mark.gpu, requires_gpu]
VRAM_LIMIT_BYTES = 7.2e9
NODE_RANGE = (22_000_000, 25_500_000)
STEPS = 5


def _reference_payload() -> dict:
    """Return a volume3d payload whose 5H grid has about 25 M nodes."""
    raw = plan_payload(dx=0.91, device="gpu", kind="volume3d")
    sim = raw["grid"]["sim"]
    sim["nz"] = math.ceil(round(5 * raw["scene"]["h_max_m"] / sim["dx_m"], 6))
    return raw


def test_25m_node_volume3d_peak_vram_is_within_7_2_gb() -> None:
    """A few steps at ~25 M nodes allocate every buffer; the pool peak stays <= 7.2 GB."""
    p = parse_payload(HeavyPayload, _reference_payload())
    sim = p.grid.sim
    nodes = int(sim.nx) * int(sim.ny) * int(sim.nz)
    assert NODE_RANGE[0] <= nodes <= NODE_RANGE[1], nodes

    case = build_volume_case(p)
    with PeakMemory("gpu") as mem:
        stepper = fastest(case.problem)
        stepper.step(STEPS, accumulate=True)
        stepper.synchronize()
        stepper.close()
    print(f"nodes {nodes} peak VRAM {mem.peak / 1e9:.2f} GB")
    assert mem.peak <= VRAM_LIMIT_BYTES
