"""SOL-15: 2D square cylinder, Re 150, 5 % blockage, D = 20 cells.

Documented bands (2D numerical literature, Sohankar et al. 1998, JFE
120; Sharma & Eswaran 2004, Num. Heat Transfer A 45): St 0.150-0.170
and mean recirculation length 1.0-1.8 D behind the rear face. The plan's
0.13-0.15 band matches 3D experiments (Okajima 1982) that a 2D model
cannot reproduce; measured St is reported in the test output.
"""

import numpy as np
import pytest

from app.services.bench.validation_cases import square_cylinder
from app.services.device.array_module import to_host
from tests.support.stepper_choice import fastest

pytestmark = pytest.mark.slow


def _run() -> tuple[float, float]:
    problem, g = square_cylinder(d=20, reynolds=150.0, u=0.1)
    ny, nx = problem.shape
    stepper = fastest(problem)
    stepper.step(int(60 * g["d"] / g["u"]))
    period = g["d"] / g["u"] / 0.15
    every = max(1, int(period // 40))
    probe = g["y_mid"] * nx + g["x_rear"] + 2 * g["d"]
    signal = []
    for _ in range(int(25 * period / every)):
        stepper.step(every, accumulate=True)
        signal.append(float(to_host(stepper.macroscopic()[1][1, probe : probe + 1])[0]))
    s = np.sign(np.asarray(signal) - np.mean(signal))
    ups = np.flatnonzero((s[:-1] < 0) & (s[1:] >= 0))
    strouhal = g["d"] / g["u"] / (np.diff(ups).mean() * every)
    line = to_host(stepper.avg_u)[0].reshape(ny, nx)[g["y_mid"], g["x_rear"]:]
    i = int(np.argmax(line > 0))
    length = (i - 1 + (-line[i - 1]) / (line[i] - line[i - 1])) / g["d"]
    print(f"square cylinder: St={strouhal:.4f} Lr/D={length:.3f}")
    return float(strouhal), float(length)


def test_strouhal_and_recirculation_length_in_literature_band() -> None:
    strouhal, length = _run()
    assert 0.150 <= strouhal <= 0.170
    assert 1.0 <= length <= 1.8
