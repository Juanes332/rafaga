"""Turn averaged lattice velocities into K/velocity fields on the output grid."""

from dataclasses import dataclass

import numpy as np

from app.services.boundary.log_profile import friction_velocity, log_speed
from app.services.lattice.lattice_problem import SOLID
from app.services.postprocess.resample_service import bilinear, blend_layers, plan_points
from app.services.simulation.simulation_case import SimulationCase
from app.services.voxelize.coverage_service import AxisGrid
from app.services.voxelize.frame_transform import WindFrame
from app.services.voxelize.voxelize_section import SectionSpec, voxelize_section
from app.services.voxelize.voxelize_service import PlanSpec, voxelize_plan


@dataclass
class OutputFields:
    """Fields on the output grid, ordered as written to disk."""

    arrays: dict[str, np.ndarray]
    mask: np.ndarray
    dx_m: float
    extent: tuple[float, float, float, float]


def uref_za_ms(case: SimulationCase) -> float:
    """Return the physical reference speed at z_a from the payload wind."""
    wind = case.payload.wind
    if wind.uref_za_ms:
        return float(wind.uref_za_ms)
    ustar = wind.ustar_ms or friction_velocity(wind.u10_ms, wind.z0_m, wind.kappa)
    return float(log_speed(wind.analysis_height_m, ustar, wind.z0_m, wind.kappa))


def _finish(case, comps: dict, mean_sq, mask: np.ndarray, names: list[str]) -> dict:
    """Scale lattice velocities to K, m/s and turbulence intensity."""
    solid = mask == SOLID
    mag = np.sqrt(sum(v * v for v in comps.values()))
    scale = uref_za_ms(case) / case.u_ref_lat
    out = {"K": mag / case.u_ref_lat}
    out.update({names[i]: v * scale for i, v in enumerate(comps.values())})
    out["speed"] = mag * scale
    if mean_sq is not None:
        sigma = np.sqrt(np.clip(mean_sq - mag * mag, 0.0, None) / 3.0)
        out["ti"] = np.where(mag > 1e-9, sigma / np.where(mag > 1e-9, mag, 1.0), np.nan)
    elif case.kind == "plan2d":
        out["ti"] = np.full(mask.shape, np.nan)
    return {k: np.where(solid, np.nan, v).astype(np.float32) for k, v in out.items()}


def plan_output(case: SimulationCase, avg_u: np.ndarray, avg_u2: np.ndarray) -> OutputFields:
    """Sample plan2d / volume3d (at z_a) fields on the north-up grid."""
    p = case.payload
    sim, out = p.grid.sim, p.grid.output
    fluid = (case.problem.mask != SOLID).astype(float)
    fields = {"ux": avg_u[0], "uy": avg_u[1], "u2": avg_u2}
    if case.kind == "volume3d":
        fields["uz"] = avg_u[2]
        fields, support = blend_layers(fields, fluid, p.wind.analysis_height_m, sim.dx_m,
                                       p.wind.z0_m)
        fluid = support.astype(float)
    grid = AxisGrid(sim.origin[0], sim.origin[1], sim.dx_m, sim.nx, int(sim.ny))
    east, north = plan_points(out.origin_x, out.origin_y, out.dx_m, out.nx, out.ny)
    s = bilinear(fields, fluid, grid, case.frame, east, north)
    ue, un = case.frame.to_enu_vector(s["ux"], s["uy"])
    comps = {"ux": ue, "uy": un}
    names = ["ux", "uy"]
    if case.kind == "volume3d":
        comps["uz"] = s["uz"]
        names.append("uz")
    out_grid = AxisGrid(out.origin_x, out.origin_y, out.dx_m, out.nx, out.ny)
    mask = voxelize_plan(p.scene, PlanSpec(out_grid, WindFrame.identity(), p.physics.supersampling),
                         p.physics.subgrid_coverage_solid).mask
    mean_sq = s["u2"] if case.kind == "volume3d" else None
    arrays = _finish(case, comps, mean_sq, mask, names)
    extent = (out.origin_x, out.origin_x + out.nx * out.dx_m, out.origin_y, out.origin_y + out.ny * out.dx_m)
    return OutputFields(arrays, mask, out.dx_m, extent)


def section_output(case: SimulationCase, avg_u: np.ndarray) -> OutputFields:
    """Sample section2d fields on the (nz, ns) output grid."""
    p = case.payload
    sim, out = p.grid.sim, p.grid.output
    rows = case.problem.shape[0]
    fluid = (case.problem.mask != SOLID).astype(float)
    grid = AxisGrid(sim.origin[0], 0.0, sim.dx_m, sim.nx, rows)
    ns, nz = int(out.ns or out.nx), int(out.nz or out.ny)
    s0 = out.s0 if out.s0 is not None else sim.origin[0]
    ss, zz = plan_points(s0, 0.0, out.dx_m, ns, nz)
    s = bilinear({"us": avg_u[0], "uz": avg_u[1]}, fluid, grid, WindFrame.identity(), ss, zz)
    spec = SectionSpec(tuple(p.section.p0), tuple(p.section.p1), s0, out.dx_m, ns, nz,
                       p.physics.supersampling)
    mask = voxelize_section(p.scene, spec, p.physics.subgrid_coverage_solid).mask
    arrays = _finish(case, {"us": s["us"], "uz": s["uz"]}, None, mask, ["us", "uz"])
    return OutputFields(arrays, mask, out.dx_m, (s0, s0 + ns * out.dx_m, 0.0, nz * out.dx_m))
