"""3D slice previews: plan at z_a with streamlines and a vertical cut (US-11)."""

from pathlib import Path

import numpy as np

from app.services.lattice.lattice_problem import SOLID
from app.services.postprocess.output_fields import OutputFields, uref_za_ms
from app.services.postprocess.preview_service import decorate_plan
from app.services.postprocess.viewer3d_service import centre_index
from app.services.render import map_style as st
from app.services.render.map_figure import draw_scalar, fill_solids, new_map, save_png
from app.services.simulation.domain_rules import MIN_TOP_H
from app.services.simulation.simulation_case import SimulationCase

# Show the vertical cut up to 5 H (the guaranteed domain top, see
# simulation/domain_rules.py) or the whole domain when it is lower.
_SECTION_HEIGHT_H = MIN_TOP_H
_SECTION_UPSTREAM_H, _SECTION_DOWNSTREAM_H = 3.0, 8.0


def _plan_slice(case: SimulationCase, fields: OutputFields, path: Path) -> None:
    """Write K at z_a with mean-flow streamlines."""
    p, extent = case.payload, fields.extent
    fig, ax = new_map(extent)
    draw_scalar(fig, ax, fields.arrays["K"], extent, st.K_CMAP,
                "K = U / U_ref(z_a) (adimensional)", vmin=0.0, smooth=True)
    ny, nx = fields.mask.shape
    xs = extent[0] + (np.arange(nx) + 0.5) * fields.dx_m
    ys = extent[2] + (np.arange(ny) + 0.5) * fields.dx_m
    ux = np.nan_to_num(fields.arrays["ux"])
    uy = np.nan_to_num(fields.arrays["uy"])
    ax.streamplot(xs, ys, ux, uy, density=1.4, color="white", linewidth=0.5, arrowsize=0.6,
                  zorder=4)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_title(f"Corte horizontal a z = {st.decimal_comma(p.wind.analysis_height_m, 1)} m "
                 "con líneas de corriente")
    decorate_plan(fig, ax, p)
    save_png(fig, path, p.render.dpi)


def section_window(case: SimulationCase) -> tuple[int, int, int]:
    """Return the (x0, x1, z1) cell window of the vertical cut."""
    dx, h = case.payload.grid.sim.dx_m, case.payload.scene.h_max_m
    nz, _, nx = case.problem.shape
    ix, _ = centre_index(case)
    x0 = max(0, int(ix - _SECTION_UPSTREAM_H * h / dx))
    x1 = min(nx, int(ix + _SECTION_DOWNSTREAM_H * h / dx))
    return x0, x1, min(nz, int(np.ceil(round(_SECTION_HEIGHT_H * h / dx, 6))))


def _vertical_slice(case: SimulationCase, avg_u: np.ndarray, path: Path) -> None:
    """Write the speed on the vertical plane along the wind through the buildings."""
    p, dx = case.payload, case.payload.grid.sim.dx_m
    ix, iy = centre_index(case)
    solid = case.problem.mask[:, iy, :] == SOLID
    u, w = avg_u[0][:, iy, :], avg_u[2][:, iy, :]
    scale = uref_za_ms(case) / case.u_ref_lat
    speed = np.where(solid, np.nan, np.hypot(u, w) * scale)
    x0, x1, z1 = section_window(case)
    s0 = (x0 - ix) * dx
    extent = (s0, s0 + (x1 - x0) * dx, 0.0, z1 * dx)
    fig, ax = new_map(extent, labels=("Distancia en la dirección del viento (m)", st.AXIS_Z))
    draw_scalar(fig, ax, speed[:z1, x0:x1], extent, st.SPEED_CMAP, "Velocidad media (m/s)",
                vmin=0.0, digits=1, smooth=True)
    ax.imshow(np.where(solid[:z1, x0:x1], 1.0, np.nan), origin="lower", extent=extent,
              cmap=st.flat_cmap(st.SOLID_COLOR), interpolation="nearest", zorder=3)
    _arrows(ax, case, (u, w, solid), (x0, x1, z1), s0)
    ax.annotate(f"Viento desde {st.decimal_comma(p.wind.wind_from_deg, 1)}° →",
                xy=(0.02, 0.93), xycoords="axes fraction", fontsize=8,
                bbox={"boxstyle": "round,pad=0.25", "fc": "white", "alpha": 0.8})
    ax.set_title("Corte vertical en la dirección del viento por el centro del conjunto")
    save_png(fig, path, p.render.dpi)


def _arrows(ax, case: SimulationCase, uws, window, s0: float) -> None:
    """Draw the in-plane mean velocity arrows of the vertical cut."""
    u, w, solid = uws
    x0, x1, z1 = window
    dx = case.payload.grid.sim.dx_m
    step = max(1, (x1 - x0) // 40)
    xs = s0 + (np.arange(x1 - x0) + 0.5) * dx
    zs = (np.arange(z1) + 0.5) * dx
    uq = fill_solids(np.where(solid, np.nan, u))[:z1, x0:x1]
    wq = fill_solids(np.where(solid, np.nan, w))[:z1, x0:x1]
    keep = ~solid[:z1, x0:x1]
    gx, gz = np.meshgrid(xs, zs)
    sel = (slice(None, None, step), slice(None, None, step))
    ax.quiver(gx[sel][keep[sel]], gz[sel][keep[sel]], uq[sel][keep[sel]], wq[sel][keep[sel]],
              color="#1d1d1b", width=0.0018, scale=40 * case.u_ref_lat, zorder=4)


def write_slice_images(case: SimulationCase, avg_u: np.ndarray, fields: OutputFields,
                       out_dir: Path) -> list[dict]:
    """Render slice_za.png and slice_xz.png; return manifest image entries."""
    images = out_dir / "images"
    images.mkdir(parents=True, exist_ok=True)
    _plan_slice(case, fields, images / "slice_za.png")
    _vertical_slice(case, avg_u, images / "slice_xz.png")
    return [{"name": n, "file": f"images/{n}.png"} for n in ("slice_za", "slice_xz")]
