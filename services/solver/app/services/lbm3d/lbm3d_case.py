"""Build the volume3d D3Q19 LES case from a payload (SOL-09)."""

# The 3D case is a hybrid RANS/LES (README "Turbulence"): damped mixing
# length in the first layers, Smagorinsky above, a synthetic turbulent
# inflow and far-field profile nudging that keeps K = 1 along the fetch.

import numpy as np

from app.models.jobs.payload_schemas import HeavyPayload
from app.services.boundary.abl_closure import hybrid_length_field, top_shear_stress
from app.services.boundary.inflow_turbulence import (
    FRAME_STEPS,
    InflowSpec,
    turbulent_inlet_bank,
)
from app.services.boundary.log_profile import (
    friction_velocity,
    lattice_inlet_profile,
    log_speed,
    profile_ratio,
    sponge_ramp,
    wall_drag_coefficient,
)
from app.services.boundary.profile_nudging import nudge_spec
from app.services.lattice.lattice_problem import LatticeProblem
from app.services.lattice.lattice_units import flow_through_steps, lattice_units
from app.services.simulation.simulation_case import (
    SimulationCase,
    plan_window,
    reynolds_warnings,
)
from app.services.voxelize.coverage_service import AxisGrid
from app.services.voxelize.frame_transform import WindFrame
from app.services.voxelize.voxelize_service import PlanSpec, voxelize_plan


def analysis_layer(z_a: float, dx: float, nz: int) -> int:
    """Return the layer index whose cell contains the analysis height."""
    return int(min(max(np.floor(z_a / dx), 0), nz - 1))


# Streamwise integral length of the inflow eddies, in building heights,
# capped in metres (surface-layer scales of 50-100 m).
_INFLOW_LENGTH_H, _INFLOW_LENGTH_CAP_M = 2.0, 100.0


def _inlet(p: HeavyPayload, nz: int, ny: int) -> np.ndarray:
    """Return the (K, 3, nz*ny) inlet bank: turbulent, or steady when disabled."""
    dx, z0, u_lat = p.grid.sim.dx_m, p.wind.z0_m, p.physics.u_lattice_ref
    profile = lattice_inlet_profile(nz, dx, z0, u_lat)
    if p.physics.inflow_perturbation <= 0:
        base = np.zeros((1, 3, nz * ny), dtype=np.float32)
        base[0, 0] = np.repeat(profile, ny)
        return base
    length = min(_INFLOW_LENGTH_H * p.scene.h_max_m, _INFLOW_LENGTH_CAP_M) / dx
    ustar = float(np.sqrt(top_shear_stress(nz, dx, z0, u_lat)))
    return turbulent_inlet_bank(InflowSpec(profile, ny, ustar, length, p.physics.seed))


def build_volume_case(p: HeavyPayload) -> SimulationCase:
    """Return the 3D case: equilibrium ABL (inlet, wall drag, top shear, l_m), sponge."""
    sim, ph, wind = p.grid.sim, p.physics, p.wind
    nz, ny = int(sim.nz), int(sim.ny)
    frame = WindFrame.from_wind(sim.wind_from_deg if sim.wind_from_deg is not None else wind.wind_from_deg)
    grid = AxisGrid(sim.origin[0], sim.origin[1], sim.dx_m, sim.nx, ny)
    vox = voxelize_plan(p.scene, PlanSpec(grid, frame, ph.supersampling, nz), ph.subgrid_coverage_solid)
    z_top = nz * sim.dx_m
    ustar = wind.ustar_ms or friction_velocity(wind.u10_ms, wind.z0_m, wind.kappa)
    units = lattice_units(ph.u_lattice_ref, sim.dx_m, float(log_speed(z_top, ustar, wind.z0_m)),
                          ph.nu_lattice_floor)
    inlet = _inlet(p, nz, ny)
    sponge = sponge_ramp(sim.nx, ph.sponge_fraction)
    problem = LatticeProblem(
        shape=vox.mask.shape, mask=vox.mask, pid=vox.pid, ptable=vox.ptable,
        sponge=sponge, inlet=inlet, tau0=units.tau0,
        smagorinsky_cs=ph.smagorinsky_cs, tau_min=ph.tau_min, tau_max=ph.tau_max,
        sponge_tau=ph.sponge_tau, bottom_wall=True,
        a_wall=wall_drag_coefficient(sim.dx_m, wind.z0_m), initial_u=inlet.mean(axis=0),
        inlet_period=FRAME_STEPS,
        mixing_length=hybrid_length_field(vox.mask, sim.dx_m, wind.z0_m, ph.smagorinsky_cs),
        ground_slip=True, top_force=top_shear_stress(nz, sim.dx_m, wind.z0_m, ph.u_lattice_ref),
        nudge=nudge_spec(vox.mask, sponge, lattice_inlet_profile(nz, sim.dx_m, wind.z0_m,
                                                                 ph.u_lattice_ref),
                         flow_through_steps(sim.nx, ph.u_lattice_ref)),
    )
    layer = analysis_layer(wind.analysis_height_m, sim.dx_m, nz)
    window = plan_window(frame, p, vox.mask[layer]) + layer * ny * sim.nx
    u_ref = ph.u_lattice_ref * float(profile_ratio(wind.analysis_height_m, z_top, wind.z0_m))
    return SimulationCase(p, problem, units, u_ref, frame, window, reynolds_warnings(p, units))
