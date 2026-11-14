"""CPU/GPU stepper tests: conservation, stability and one-step parity."""

import numpy as np
import pytest

from app.services.lattice.numpy_stepper import CpuStepper
from tests.support.gpu_marks import requires_gpu
from tests.support.lattice_factory import make_problem


def test_cpu_uniform_flow_without_obstacles_stays_uniform() -> None:
    problem = make_problem((12, 40), with_obstacles=False, bottom_wall=False)
    problem.inlet = problem.inlet[:1]
    stepper = CpuStepper(problem, threads=2)
    stepper.step(50)
    rho, u = stepper.macroscopic()
    assert np.allclose(u[0], 0.05, atol=2e-4)
    assert np.allclose(rho, 1.0, atol=1e-3)


def test_cpu_accumulates_running_mean() -> None:
    stepper = CpuStepper(make_problem((10, 30)), threads=2)
    stepper.step(5, accumulate=True)
    assert stepper.count == 5
    assert np.isfinite(stepper.avg_u).all() and stepper.avg_u[0].max() > 0


@pytest.mark.parametrize("shape", [(16, 48), (8, 10, 32)])
def test_cpu_obstacle_flow_stays_finite(shape) -> None:
    stepper = CpuStepper(make_problem(shape), threads=3)
    stepper.step(60)
    assert np.isfinite(stepper.f).all()


def test_top_force_drives_a_slip_channel_and_slip_ground_keeps_it_uniform() -> None:
    problem = make_problem((6, 4, 12), with_obstacles=False, abl=True)
    problem.mixing_length = None
    problem.a_wall = 0.0
    problem.inlet = problem.inlet[:1]
    problem.sponge[:] = 0
    stepper = CpuStepper(problem, threads=2)
    stepper.step(40)
    _, u = stepper.macroscopic()
    ux = u[0].reshape(problem.shape)
    assert ux[-1, :, 4:8].mean() > 0.05 + 10 * 2e-5
    assert np.allclose(ux[0, :, 4:8], 0.05, atol=2e-4)


def test_nudging_force_speeds_up_a_flow_slower_than_its_target() -> None:
    def run(nudge: bool) -> float:
        problem = make_problem((6, 10, 24), with_obstacles=False, abl=True, nudge=nudge)
        problem.mixing_length = None
        problem.inlet = problem.inlet[:1]
        stepper = CpuStepper(problem, threads=2)
        stepper.step(200)
        _, u = stepper.macroscopic()
        return float(u[0].reshape(problem.shape)[:, :, 6:14].mean())

    assert run(True) > run(False) + 1e-4


def test_mixing_length_raises_the_relaxation_time() -> None:
    from app.services.lattice.numpy_collision import relaxation_time

    pi = np.full((3, 2), 1e-3, dtype=np.float32)
    weight = np.ones(3, dtype=np.float32)
    rho = np.ones(2, dtype=np.float32)
    params = {"tau0": 0.5005, "tau_min": 0.5005, "tau_max": 2.0}
    small = relaxation_time(pi, weight, rho, params | {"cs2": np.float32(0.17**2)})
    big = relaxation_time(pi, weight, rho, params | {"cs2": np.array([0.17**2, 4.0], np.float32)})
    assert big[1] > small[1] and big[0] == pytest.approx(small[0])


@pytest.mark.gpu
@requires_gpu
@pytest.mark.parametrize("shape,abl,nudge", [((17, 41), False, False), ((9, 11, 33), False, False),
                                             ((17, 41), True, False), ((9, 11, 33), True, False),
                                             ((9, 11, 33), True, True)])
def test_gpu_matches_cpu_after_several_steps(shape, abl, nudge) -> None:
    from app.services.lattice.cuda_stepper import GpuStepper

    cpu = CpuStepper(make_problem(shape, seed=3, abl=abl, nudge=nudge), threads=2)
    gpu = GpuStepper(make_problem(shape, seed=3, abl=abl, nudge=nudge))
    steps = 47 if nudge else 7
    cpu.step(steps, accumulate=True)
    gpu.step(steps, accumulate=True)
    assert np.allclose(gpu.f.get(), cpu.f, atol=2e-6, rtol=1e-5)
    assert np.allclose(gpu.avg_u.get(), cpu.avg_u, atol=2e-6)
