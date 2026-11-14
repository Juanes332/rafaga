"""Physical and numerical constants frozen into every job payload."""

KAPPA = 0.41
U10_NOMINAL = 10.0
U_LATTICE_REF = 0.05
BYTES_PER_NODE = {"plan2d": 104, "section2d": 104, "volume3d": 224}
OVERHEAD_BYTES = 512 * 1024 * 1024
GPU_VRAM_FRACTION = 0.85
DX_STEP = 0.25
MIN_BUILDING_CELLS = 4
Z0_REF_M = 0.03
BLENDING_HEIGHT_M = 60.0
MAX_DIRECTIONS = 16

# Time model (ADR-10), calibrated on an RTX 4060 against the solver benchmark and real runs:
#   seconds = FIXED_OVERHEAD_S + sum_over_jobs( lattice_updates / (MLUPS_eff * 1e6) )
#   MLUPS_eff = PEAK_FRACTION * measured_mlups * N / (N + N_HALF)   (small grids under-fill the GPU)
# 3D: ~879 MLUPS at large grids vs 947 measured at start-up -> PEAK_FRACTION 0.93; a 2.74 M-node
# run took 81 s (10 s fixed: process start, CuPy JIT, post-processing and PNGs).
# 2D: runs of 3.6-5 s against a 6 s raw estimate -> STEP_SCALE 0.5 with 1.5 s fixed.
FIXED_OVERHEAD_S = {"plan2d": 1.5, "section2d": 1.5, "volume3d": 10.0}
PEAK_FRACTION = {"plan2d": 1.0, "section2d": 1.0, "volume3d": 0.93}
N_HALF_NODES = {"plan2d": 0.0, "section2d": 0.0, "volume3d": 1_200_000}
# Conservative CPU throughput (ADR-16/ADR-28) used while the node reports no measured MLUPS.
CPU_FALLBACK_MLUPS = {"plan2d": 20.0, "section2d": 20.0, "volume3d": 5.0}
STEP_SCALE = {"plan2d": 0.5, "section2d": 0.5, "volume3d": 1.0}


def physics(kind: str) -> dict:
    """Return the physics block of the job contract."""
    return {
        "u_lattice_ref": U_LATTICE_REF, "nu_lattice_floor": 5e-05,
        "smagorinsky_cs": 0.17, "tau_min": 0.5005, "tau_max": 2.0,
        "collision": "regularized_bgk", "sponge_fraction": 0.10, "sponge_tau": 1.0,
        "inflow_perturbation": 0.02 if kind == "volume3d" else 0.0,
        "seed": 12345, "max_local_mach": 0.35,
        "subgrid_coverage_solid": 0.5, "supersampling": 4,
    }


def convergence(kind: str) -> dict:
    """Return the convergence block (ADR-11)."""
    spin, cap = (1.5, 6.0) if kind == "volume3d" else (2.0, 8.0)
    return {"spinup_ft": spin, "min_avg_ft": 2.0, "max_avg_ft": cap,
            "check_every_ft": 0.25, "tolerance": 0.01, "consecutive": 3}
