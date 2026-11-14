"""Empty-domain ABL: K at z_a stays at 1 +-10 % and the LES is turbulent."""

import numpy as np
import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.device.array_module import to_host
from app.services.lattice.lattice_units import flow_through_steps
from app.services.lbm3d.lbm3d_case import build_volume_case
from app.services.postprocess.output_fields import plan_output
from app.services.simulation.simulation_runner import SimulationRunner
from tests.support.gpu_marks import requires_gpu
from tests.support.scenario_factory import SceneBuilder, heavy_payload
from tests.support.stepper_choice import fastest

pytestmark = [pytest.mark.slow, pytest.mark.gpu, requires_gpu]
SCHEDULE = {"spinup_ft": 2.0, "min_avg_ft": 2.0, "max_avg_ft": 2.0, "check_every_ft": 0.25,
            "tolerance": 0.01, "consecutive": 3}


@pytest.fixture(scope="module")
def empty_run():
    scene = SceneBuilder().build(phantom=(0.0, 0.0, 30.0, 20.0, 15.0))
    raw = heavy_payload(scene, "volume3d", 270.0, 3.0, SCHEDULE)
    case = build_volume_case(parse_payload(HeavyPayload, raw))
    stepper = fastest(case.problem)
    SimulationRunner(case, stepper, lambda *_: False).run()
    shape = case.problem.shape
    fields = plan_output(case, to_host(stepper.avg_u).reshape((3,) + shape),
                         to_host(stepper.avg_u2).reshape(shape))
    series = _streamwise_series(case, stepper)
    stepper.close()
    return fields, series


def _streamwise_series(case, stepper) -> np.ndarray:
    """Return u_x(t) on the first layer (z = 1.5 m) inside the output window."""
    nodes = case.window[case.window < case.problem.nx * case.problem.shape[1]]
    samples = []
    for _ in range(flow_through_steps(case.problem.nx, 0.05) // 10):
        stepper.step(10)
        samples.append(to_host(stepper.macroscopic()[1][0, nodes]))
    return np.asarray(samples)


def test_empty_domain_keeps_k_within_ten_percent_along_the_fetch(empty_run) -> None:
    fields, _ = empty_run
    k_cols = np.nanmean(fields.arrays["K"], axis=0)
    print("K along fetch:", np.round(k_cols[::4], 3))
    assert np.all(np.abs(k_cols - 1.0) <= 0.10)


def test_far_field_turbulence_intensity_is_urban_at_pedestrian_height(empty_run) -> None:
    fields, series = empty_run
    iu = float(np.mean(series.std(axis=0) / series.mean(axis=0)))
    ti = float(np.nanmean(fields.arrays["ti"]))
    print(f"far field at z = 1.5 m: Iu = {iu:.3f}, ti field = {ti:.3f}")
    assert 0.15 <= iu <= 0.30
    assert 0.12 <= ti <= 0.30
