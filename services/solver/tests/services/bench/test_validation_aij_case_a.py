"""SOL-16: AIJ case A, 1:1:2 building in an ABL, qualitative recirculation."""

from pathlib import Path

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from app.services.bench.validation_cases import aij_case_a
from app.services.device.array_module import to_host
from app.services.lattice.lattice_units import flow_through_steps
from tests.support.gpu_marks import HAS_GPU
from tests.support.stepper_choice import fastest

pytestmark = pytest.mark.slow
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"


def _plot(u: np.ndarray, g: dict) -> None:
    fig = Figure(figsize=(9, 3.5), layout="constrained")
    FigureCanvasAgg(fig)
    ax = fig.add_subplot()
    image = ax.imshow(u[:, g["y_mid"], :] / 0.05, origin="lower", cmap="RdBu_r", vmin=-1, vmax=1)
    ax.contour(u[:, g["y_mid"], :], levels=[0.0], colors="k", linewidths=0.6)
    fig.colorbar(image, ax=ax, label="u / u_ref")
    ax.set_title("AIJ caso A: u media en el plano central")
    ARTIFACTS.mkdir(exist_ok=True)
    fig.savefig(ARTIFACTS / "aij_case_a_centerplane.png", dpi=120)


def test_wake_reattaches_between_1_and_2_5_h_and_roof_separates() -> None:
    problem, g = aij_case_a(b=12 if HAS_GPU else 6)
    stepper = fastest(problem)
    ft = flow_through_steps(problem.nx, 0.05)
    stepper.step(int(1.5 * ft))
    stepper.step(3 * ft, accumulate=True)
    nz, ny, nx = problem.shape
    u = to_host(stepper.avg_u)[0].reshape(nz, ny, nx)
    _plot(u, g)
    h, rear = g["h"], g["x0"] + g["b"]
    line = u[max(int(0.125 * h), 0), g["y_mid"], rear:]
    reverse = np.flatnonzero(line < 0)
    assert reverse.size > 0
    tail = line[reverse[0]:]
    reattach = (reverse[0] + int(np.argmax(tail > 0))) / h
    print(f"AIJ case A: reattachment {reattach:.2f} H behind the leeward face")
    assert 1.0 <= reattach <= 2.5
    roof = u[h, g["y_mid"], g["x0"] : rear]
    assert (roof < 0).any()
