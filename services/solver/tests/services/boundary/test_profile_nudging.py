"""Far-field profile nudging: a PI controller on the lateral strips."""

import numpy as np

from app.services.boundary.profile_nudging import ProfileNudger, nudge_spec
from app.services.lattice.lattice_constants import lattice_for_dim
from app.services.lattice.lattice_problem import SOLID, equilibrium

NZ, NY, NX = 4, 20, 12


def _sponge() -> np.ndarray:
    s = np.zeros(NX, dtype=np.float32)
    s[-2:] = [0.5, 1.0]
    return s


def _populations(ux: float) -> np.ndarray:
    lat = lattice_for_dim(3)
    n = NZ * NY * NX
    u = np.zeros((3, n), dtype=np.float32)
    u[0] = ux
    return equilibrium(lat, np.ones(n, dtype=np.float32), u)


def _nudger(mask: np.ndarray | None = None) -> ProfileNudger:
    mask = np.zeros((NZ, NY, NX), dtype=np.uint8) if mask is None else mask
    spec = nudge_spec(mask, _sponge(), np.full(NZ, 0.05, dtype=np.float32), ft_steps=200)
    return ProfileNudger(spec, np, lattice_for_dim(3).c[:, 0])


def test_strips_hug_the_lateral_faces_and_skip_solids_and_sponge() -> None:
    mask = np.zeros((NZ, NY, NX), dtype=np.uint8)
    mask[:, :, 3] = SOLID
    spec = nudge_spec(mask, _sponge(), np.full(NZ, 0.05), ft_steps=200)
    y = (spec.strip_nodes // NX) % NY
    assert set(np.unique(y)) == {0, 1, NY - 2, NY - 1}
    assert not np.any(mask.reshape(-1)[spec.strip_nodes] == SOLID)
    live = spec.live.reshape(NZ, NX)
    assert not live[:, 3].any() and not live[:, -2:].any() and live[:, :3].all()


def test_slow_strips_get_a_positive_force_only_where_live() -> None:
    nudger = _nudger()
    nudger.update(_populations(0.04))
    fx = nudger.fxz.reshape(NZ, NX)
    assert np.all(fx[:, :-2] > 0)
    assert np.all(fx[:, -2:] == 0)


def test_matched_strips_get_no_force() -> None:
    nudger = _nudger()
    nudger.update(_populations(0.05))
    assert np.abs(nudger.fxz).max() < 1e-9


def test_integral_term_grows_while_the_error_persists() -> None:
    nudger = _nudger()
    nudger.update(_populations(0.04))
    first = float(nudger.fxz[0])
    for _ in range(5):
        nudger.update(_populations(0.04))
    assert float(nudger.fxz[0]) > first


def test_force_is_bounded() -> None:
    nudger = _nudger()
    for _ in range(2000):
        nudger.update(_populations(0.0))
    assert float(nudger.fxz.max()) <= 2.0 * 0.05 / nudger.spec.p_steps * (1 + 1e-5)
