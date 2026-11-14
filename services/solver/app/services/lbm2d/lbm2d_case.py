"""Build plan2d and section2d D2Q9 cases from a payload (SOL-07, SOL-08)."""

import numpy as np

from app.models.jobs.payload_schemas import HeavyPayload
from app.services.boundary.abl_closure import mixing_length_field, top_shear_stress
from app.services.boundary.log_profile import (
    friction_velocity,
    lattice_inlet_profile,
    log_speed,
    profile_ratio,
    sponge_ramp,
    wall_drag_coefficient,
)
from app.services.lattice.lattice_problem import SOLID, LatticeProblem
from app.services.lattice.lattice_units import lattice_units
from app.services.simulation.domain_rules import widened_payload
from app.services.simulation.simulation_case import (
    SimulationCase,
    plan_representability_warnings,
    plan_window,
    reynolds_warnings,
)
from app.services.voxelize.coverage_service import AxisGrid

PLAN_MIXING_CAP_H = 0.1
from app.services.voxelize.frame_transform import WindFrame
from app.services.voxelize.voxelize_section import SectionSpec, voxelize_section
from app.services.voxelize.voxelize_service import PlanSpec, Voxels, voxelize_plan


def _problem(p: HeavyPayload, vox: Voxels, inlet: np.ndarray, tau0: float,
             wall: float | None) -> LatticeProblem:
    """Assemble the D2Q9 problem shared by plan and section."""
    ph = p.physics
    return LatticeProblem(
        shape=vox.mask.shape, mask=vox.mask, pid=vox.pid, ptable=vox.ptable,
        sponge=sponge_ramp(vox.mask.shape[1], ph.sponge_fraction), inlet=inlet,
        tau0=tau0, smagorinsky_cs=ph.smagorinsky_cs, tau_min=ph.tau_min,
        tau_max=ph.tau_max, sponge_tau=ph.sponge_tau, bottom_wall=wall is not None,
        a_wall=wall or 0.0,
    )


def build_plan_case(p: HeavyPayload) -> SimulationCase:
    """Return the plan case: uniform U_ref(z_a) inlet, free-slip sides."""
    p = widened_payload(p)
    sim, ph, wind = p.grid.sim, p.physics, p.wind
    frame = WindFrame.from_wind(sim.wind_from_deg if sim.wind_from_deg is not None else wind.wind_from_deg)
    grid = AxisGrid(sim.origin[0], sim.origin[1], sim.dx_m, sim.nx, sim.ny)
    vox = voxelize_plan(p.scene, PlanSpec(grid, frame, ph.supersampling), ph.subgrid_coverage_solid)
    ustar = wind.ustar_ms or friction_velocity(wind.u10_ms, wind.z0_m, wind.kappa)
    u_phys = float(log_speed(wind.analysis_height_m, ustar, wind.z0_m, wind.kappa))
    units = lattice_units(ph.u_lattice_ref, sim.dx_m, u_phys, ph.nu_lattice_floor)
    inlet = np.zeros((1, 2, sim.ny), dtype=np.float32)
    inlet[0, 0] = ph.u_lattice_ref
    problem = _problem(p, vox, inlet, units.tau0, None)
    # Plan 2D has no vortex stretching: grid-sized wake vortices spin up
    # until Ma > 0.35 (a scenario run diverged at 22.5 deg). A wall-distance
    # mixing length capped at 0.1 H adds the missing 3D dissipation.
    problem.mixing_length = mixing_length_field(
        vox.mask, sim.dx_m, 0.0, ph.smagorinsky_cs, ground=False,
        cap_m=PLAN_MIXING_CAP_H * p.scene.h_max_m)
    warnings = reynolds_warnings(p, units) + plan_representability_warnings(p)
    return SimulationCase(p, problem, units, ph.u_lattice_ref, frame,
                          plan_window(frame, p, vox.mask), warnings)


def build_section_case(p: HeavyPayload) -> SimulationCase:
    """Return the (s, z) case: log-law inlet, ground wall function, slip top."""
    sim, ph, wind = p.grid.sim, p.physics, p.wind
    rows = sim.nz or sim.ny
    spec = SectionSpec(tuple(p.section.p0), tuple(p.section.p1), sim.origin[0], sim.dx_m,
                       sim.nx, rows, ph.supersampling)
    vox = voxelize_section(p.scene, spec, ph.subgrid_coverage_solid)
    z_top = rows * sim.dx_m
    ustar = wind.ustar_ms or friction_velocity(wind.u10_ms, wind.z0_m, wind.kappa)
    units = lattice_units(ph.u_lattice_ref, sim.dx_m, float(log_speed(z_top, ustar, wind.z0_m)),
                          ph.nu_lattice_floor)
    inlet = np.zeros((1, 2, rows), dtype=np.float32)
    inlet[0, 0] = lattice_inlet_profile(rows, sim.dx_m, wind.z0_m, ph.u_lattice_ref)
    problem = _problem(p, vox, inlet, units.tau0, wall_drag_coefficient(sim.dx_m, wind.z0_m))
    problem.mixing_length = mixing_length_field(vox.mask, sim.dx_m, wind.z0_m, ph.smagorinsky_cs)
    problem.ground_slip = True
    problem.top_force = top_shear_stress(rows, sim.dx_m, wind.z0_m, ph.u_lattice_ref)
    u_ref = ph.u_lattice_ref * float(profile_ratio(wind.analysis_height_m, z_top, wind.z0_m))
    window = np.flatnonzero(vox.mask.reshape(-1) != SOLID)
    return SimulationCase(p, problem, units, u_ref, None, window, reynolds_warnings(p, units))
