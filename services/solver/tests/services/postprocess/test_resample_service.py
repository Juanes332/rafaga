"""Tests for output-grid resampling."""

import numpy as np

from app.services.postprocess.resample_service import bilinear, blend_layers, plan_points
from app.services.voxelize.coverage_service import AxisGrid
from app.services.voxelize.frame_transform import WindFrame


def test_linear_field_is_reproduced_exactly_inside() -> None:
    sim = AxisGrid(0.0, 0.0, 1.0, 20, 10)
    xs = np.arange(20) + 0.5
    f = np.tile(xs, (10, 1))
    east, north = plan_points(2.0, 2.0, 1.0, 5, 5)
    out = bilinear({"f": f}, np.ones((10, 20)), sim, WindFrame.identity(), east + 0.25, north)
    assert np.allclose(out["f"], east + 0.25)


def test_rotated_frame_maps_points_into_sim_coordinates() -> None:
    frame = WindFrame.from_wind(0.0)  # flow toward south: sim x = -north
    sim = AxisGrid(-10.0, -10.0, 1.0, 20, 20)
    xs = np.arange(20) - 9.5
    f = np.tile(xs, (20, 1))
    out = bilinear({"f": f}, np.ones((20, 20)), sim, frame, np.array([0.0]), np.array([3.0]))
    assert np.allclose(out["f"], -3.0)


def test_points_without_fluid_support_are_nan() -> None:
    sim = AxisGrid(0.0, 0.0, 1.0, 4, 4)
    fluid = np.ones((4, 4))
    fluid[1:3, 1:3] = 0
    out = bilinear({"f": np.ones((4, 4))}, fluid, sim, WindFrame.identity(),
                   np.array([2.0, 0.5]), np.array([2.0, 0.5]))
    assert np.isnan(out["f"][0]) and out["f"][1] == 1.0


def test_blend_layers_interpolates_in_z() -> None:
    f = np.stack([np.zeros((2, 2)), np.ones((2, 2))])
    out, ok = blend_layers({"f": f}, np.ones((2, 2, 2)), z=1.0, dx=1.0)
    assert np.allclose(out["f"], 0.5) and ok.all()


def test_blend_layers_follows_the_log_law_below_the_second_layer() -> None:
    dx, z0, z_a = 2.0, 1.0, 1.5
    zc = (np.arange(4) + 0.5) * dx
    f = np.log((zc + z0) / z0)[:, None, None] * np.ones((4, 2, 2))
    out, ok = blend_layers({"f": f}, np.ones((4, 2, 2)), z=z_a, dx=dx, z0=z0)
    assert np.allclose(out["f"], np.log((z_a + z0) / z0), rtol=1e-6) and ok.all()


def test_blend_layers_extrapolates_log_law_under_the_first_centre() -> None:
    dx, z0, z_a = 4.0, 1.0, 1.5
    zc = (np.arange(3) + 0.5) * dx
    f = np.log((zc + z0) / z0)[:, None, None] * np.ones((3, 1, 1))
    out, _ = blend_layers({"f": f}, np.ones((3, 1, 1)), z=z_a, dx=dx, z0=z0)
    assert np.allclose(out["f"], np.log((z_a + z0) / z0), rtol=1e-6)
