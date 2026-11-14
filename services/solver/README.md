# Ráfaga solver

Queue worker that runs the lattice-Boltzmann simulations and produces every numeric
artefact (fields, previews, Lawson comfort, export PNGs, PDF reports). Its only HTTP route
is `GET /health`. It speaks to the rest of the system exclusively through the shared
Postgres tables and the `/data` volume described in
`docs/architecture/contracts/job-contract.md` (contract v1).

## Layout

```
app/
  configs/config.py                  environment settings
  core/{errors,logging,db}/          error codes (contract 4.1), JSON logs, connections
  models/{health,jobs,scene}/        /health schema, job payloads, canonical scene
  routers/health/health_router.py    GET /health
  repositories/{jobs,results,nodes}/ SQL of contract section 4 (verbatim claim statement)
  services/
    queue/        supervisor, heavy lane (spawned child), light lane, completion + aggregate rule
    device/       array module (CuPy|NumPy), probe, capabilities, memory guard, device selection
    lattice/      D2Q9/D3Q19 tables, CUDA kernels (*.cu), NumPy twin, steppers, units
    voxelize/     scene -> mask / porous ids (plan, section, volume)
    boundary/     shifted log law, inlet bank, wall function, sponge
    porous/       Idelchik screens, vegetation drag
    lbm2d/ lbm3d/ case builders for plan2d, section2d, volume3d
    convergence/  ADR-11 monitor
    simulation/   heavy job orchestration and time loop
    postprocess/  output-grid resampling, fields, previews, viewer3d, manifest, comparability
    comfort/      Lawson aggregate
    render/       map figures, export PNG
    report/       WeasyPrint PDF (Literata + Hanken Grotesk, OFL, in report/fonts)
    bench/        benchmark runner, versioned cases, validation problems
```

## Physics model

* **Lattices**: D2Q9 (plan at z_a, vertical section) and D3Q19 (volume), float32 on both devices.
* **Collision**: regularized BGK with local Smagorinsky (Hou et al.), C_s = 0.17,
  tau clamped to [0.5005, 2.0] (ADR-14). Units: u_lat = 0.05, nu_lat = max(nu dt/dx^2, 5e-5).
  The length scale is per node: max(C_s dx, l_m). plan2d: l_m = kappa min(d_wall, 0.1 H)
  (2D has no vortex stretching; grid-sized wake vortices otherwise grew past Ma 0.35 and a
  scenario run diverged, `test_plan_stability`). section2d/volume3d: see below.
* **Equilibrium ABL (deviation from ADR-12 / C-3, section2d)**: a coarse LES
  (H/dx ~ 9) cannot carry the surface-layer stress with C_s dx, so the log inflow decayed
  along the fetch (empty-domain K at z_a fell 0.48 -> 0.40). section2d therefore keeps the
  Richards & Hoxey closure: Prandtl mixing length l_m = kappa min(z + z0, d_wall),
  specular (slip) ground with the matched log-law drag on the first layer, and the inlet's
  shear u*^2 applied as a streamwise force on the top layer. It is steady (2D has no
  resolved turbulence; Lawson uses the 2D default I = 0.25). Superseded for volume3d by the
  hybrid RANS/LES closure below (ADR-27 amendment).
* **Turbulence, volume3d (hybrid RANS/LES; deviation from ADR-12 / C-3)**. The previous
  3D model was the mixing-length closure above: steady, resolved `ti` ~ 0.001 in the far
  field, Lawson G = 1 on ~97 % of a single-block window. Now
  (`boundary/{abl_closure,inflow_turbulence,profile_nudging}.py`):
  * SGS: the first `RANS_LAYERS` = 6 cells keep 0.8 x kappa min(z + z0, d_wall) (the
    resolved stress adds to the modelled one there, so the RANS length is damped; 0.8 was
    calibrated on the empty domain); above, plain Smagorinsky C_s dx. Pure Smagorinsky
    down to the ground stalled the first layer (K 0.5-0.7, log-layer mismatch); a wall
    model sampled at layers 1-3 (Kawai-Larsson) made it worse (K < 0.2).
  * Inflow: synthetic turbulence, digital filter (Klein 2003) + Lund transform onto a
    neutral ABL: sigma_u = 2.5 u* capped at 0.22 U(z) (the shifted log law has U -> 0 at
    the ground), sigma_v = 0.75 sigma_u, sigma_w = 0.5 sigma_u, <u'w'> = -u*^2
    (realizability-capped). Integral length 2 H (<= 100 m); one frame per 20 steps (one
    cell of frozen turbulence at u_lat), 64-512 frames, <= 64 MiB, wrapping in time,
    built on the CPU from `physics.seed` so both devices see the same inflow.
    `physics.inflow_perturbation` is now a switch: > 0 turbulent (the API sends 0.02),
    0 steady log inflow; its amplitude is not used.
  * Far-field nudging: the hybrid ground layer is not in exact equilibrium with the
    log-law inflow (unforced, K at z_a drifted 10-15 % down along the fetch). A PI
    controller (P 0.5 FT, I 1 FT, EMA 0.1 FT, every 20 steps) compares u_x averaged over the
    outer 10 % of each lateral side (fluid cells, away from buildings) with the inlet
    profile for every (z, x) and applies the difference as a body force on the whole
    (z, x) line, like a large-scale pressure gradient; none in the sponge.
  * Ground: slip + log-law wall drag on the first layer and top shear force, as above.
  * Measured (GPU, `test_abl_homogeneity`, `test_les_block`, z0 = 1 m): empty domain,
    K at z_a 0.93-1.03 along the output window (dx = 3 m), streamwise Iu = 0.18 and
    `ti` = 0.14 at z = 1.5 m; dx = 2 m probes: Iu 0.18-0.27 at z = 1 m, K 0.93-1.06 below
    18 m. 18 m cube, dx = 2 m: lateral far field K 1.07, far-field `ti` 0.25, wake `ti`
    0.78, G > 1 on 41 % of the window, corner K max 1.59, wake reattachment 1.8-2.2 H
    (spike). Comfort therefore drops from "all A" where wakes and corners are gusty.
  * Costs: the short, over-diffused mixing-length wakes are replaced by longer LES wakes (K still 0.7 at
    6.5 H behind a cube); the near-wall layer is modelled, not resolved (H/dx ~ 9).
    CPU and GPU runs are chaotic: means agree statistically, not bit-for-bit. A screen
    across an 8 m passage between 24 m blocks: open passage K 0.85 -> 0.60, the screen
    now removes ~12 % more (mixing-length model: 0.85 -> 0.60, -30 %).
* **Forcing**: Guo scheme. The regularized projection drops the first moment of f - feq
  (= -F/2); its relaxed part is added back so the momentum gain per step is exactly F.
  Quadratic drags (screens, vegetation, ground wall function) are solved **exactly
  implicitly**: |u| + (a/2)|u|^2 = |u*|. This is the stable limit of ADR-13's
  semi-implicit update; the linearised form over-predicts the loss by up to 33 % at
  beta = 0.2, the exact one meets ±2 %.
* **Boundaries** (ADR-12): regularized velocity inlet at rho = 1 (uniform in plan; shifted log law
  scaled to u_lat at the domain top in section/3D, plus synthetic turbulence in 3D, see
  above), regularized rho = 1 outlet + linear sponge over the last 10 % of nx, specular
  free-slip sides/top, half-way bounce-back on solids, ground = specular + log-law wall drag
  on the first fluid layer (see equilibrium ABL below). Deviation: ADR-12 extrapolates the inlet density from the first
  interior cell; that traps acoustic waves between inlet and free-slip sides (+-6 %
  density striations, peaks past the Mach guard), so the inlet density is pinned to 1.
* **Porosity / sub-grid solids** (ADR-13): coverage is the exact covered fraction of each
  cell quantized to the supersampling resolution (1/16 in plan, 1/64 in 3D) with any
  non-zero overlap kept at one sample, so 0.15 m fins never vanish between samples.
  Coverage >= 0.5 -> wall. Deviation: solids thinner than half a cell (fins, canopies)
  are **plates**: their open fraction is 1 - in-plane coverage (not 1 - volume coverage,
  which made a 0.3 m canopy in a 2 m cell 85 % open and fins/canopies had no effect), so a
  fully crossed cell is near-impermeable (beta = 0.05) along the plate normal and free
  along it. Partial edge cells of thick blocks keep beta = 1 - coverage.
* **Screens / celosías** (ADR-13): Idelchik zeta(beta) spread over a band one cell wide.
  Deviation: the band was centred on the screen, so a celosía 0.5 m off a facade
  (catalogue default) reached into the wall cells and lost 25-50 % of its zeta at
  dx = 2 m. The voxelizer now keeps, of the centred and the two one-sided bands, the one
  that falls least on solid cells (integral of the resistance across the screen = zeta/2
  within 10 %, `test_facade_screen_keeps_its_full_resistance_next_to_the_wall`).
  Diagnosis of "the celosía does nothing": the porous model works (free 3 m screen
  perpendicular to the wind, beta = 0.4: lee K -28 to -35 % at dx 1-2 m; parallel: 0 %,
  `test_facade_effects`). A celosía on a windward facade sits in the stagnation zone,
  where the flow is downwash (vertical) and lateral, i.e. tangential to the screen,
  so its effect on pedestrian K is physically small (< 1 % at offsets 0.5-2 m, heights
  3-9 m, 18 m tower). It acts where the wind crosses it: free-standing, across passages,
  on lateral openings.
* **Convergence** (ADR-11): spin-up, running mean, checks every 0.25 FT on the
  fluid cells of the output window at z_a; progress follows contract section 4.
  Deviation: plan2d averages exactly `max_avg_ft` (`convergence.averaging = "fixed"`), so
  base and alternatives share one averaging window (2D wakes shed; adaptive stopping
  ended comparable runs anywhere between 4 and 8 FT, a few at the cap). The ADR-11 test
  is still evaluated at the end and reported in `converged` / `convergence_cap_reached`.
  3D/section keep adaptive stopping. With the 3D LES the windowed mean converges
  slower; runs that hit `max_avg_ft` report `convergence_cap_reached`.
* **3D domain top**: contract grids give 6 H (stretched for blockage), e.g. 7.9 H in the
  test study (the "2.5 H" seen before was only the height drawn in `slice_xz.png`). The
  solver guarantees >= 5 H (`domain_rules.raised_top_payload`): lower tops are raised
  as far as the device budget allows, otherwise warning `domain_top_capped`.
  `slice_xz.png` now shows up to 5 H (or the whole domain if lower).
* **Plan 2D domain width** (deviation from contract 3.2, which the solver otherwise takes
  as is): the plan lattice is widened symmetrically until W/Ly <= 5 % (W = cross-wind
  width of the base buildings), the 2D analogue of the 3 % blockage rule; at the
  contract's 5H margins W/Ly was ~20 % and slip sides pushed K > 1.2 bands to the edges.
  Output grid and comparability are unchanged; nodes grow ~4x (cheap on GPU, slower on
  CPU). Sides stay specular free-slip.
* **Warnings**: `low_reynolds` only when Re_H with the floored viscosity < 1.1e4 (Snyder's
  sharp-edge limit; H < 11 cells), not ADR-14's 2e4 which fired on every default mesh.
  plan2d adds `element_not_representable_2d` (ref = element id) for canopies and any
  facade element that does not cross z_a: they act through the facade downwash.
* **Guards**: every 100 steps. NaN, local Mach > 2 x `max_local_mach`, or Mach above
  `max_local_mach` on 3 consecutive checks -> `numerical_instability`. Isolated spikes
  (grid-sized 2D vortex cores crossing Ma 0.35 for < 300 steps) are tolerated and
  reported as warning `local_mach_spikes`.
* **K** = |U| / U_ref(z_a) on the north-up output grid (bilinear from the rotated sim grid;
  in 3D the vertical step is linear in ln((z + z0)/z0), exact for the wall-function log
  law, and below the first cell centre it extrapolates the log law, so z_a = 1.5 m is
  sampled correctly at dx = 2 m); `ti` = sqrt((<|u|^2> - |<u>|^2)/3) / |<u>| (3D only),
  from the resolved fluctuations of the time average (mean + std, Lawson GEM
  G = max(1, (1 + 3 ti)/1.85)).
* **Lawson**: verified against hand-computed cases (`test_lawson_model`). With ERA5 U10 over
  z0_ref = 0.03 m and site z0 = 1 m, U(1.5 m) = 0.29 U10 (ADR-15 T). In 2D (I = 0.25,
  G = 1) a mild site can legitimately be all class A; in 3D G > 1 wherever ti > 0.28.

## Device selection

`RAFAGA_DEVICE` = `auto` (GPU if CuPy can run a kernel), `cpu` (forces NumPy) or `gpu`
(fails jobs with `device_unavailable` when no GPU). A job's `payload.device` overrides
`auto`. The supervisor never touches CUDA: capabilities (probe + <= 5 s MLUPS micro
benchmark) are measured in a spawned process and upserted in `solver_nodes` every 5 s.

`python -m app.services.device.device_probe` prints
`{"ok", "gpu_name", "vram_total_bytes", "vram_free_bytes", "cuda_runtime", "driver"}` and
exits 0 only after a RawKernel produced the right result.

## Job lanes (ADR-22)

* **heavy** (`plan2d`, `section2d`, `volume3d`): one job at a time in a `spawn` child.
  Progress/heartbeat every second, cooperative cancel (<= 1 s), terminate at 8 s, kill at 9 s,
  temp output removed. A crashed child fails the job with `internal_error`
  (`error_details.reason = "solver_crashed"`).
* **light** (`aggregate`, `render`, `report`): `LIGHT_LANE_CONCURRENCY` threads, CPU only.
* Wake-up: `LISTEN rafaga_jobs` plus 2 s polling. Orphans (running, heartbeat > 60 s) are
  failed `worker_restarted`, `resumable = true` at start and their output is removed.
* When the last heavy job of a study ends, the same transaction (study row `FOR UPDATE`)
  inserts the aggregate job from `studies.aggregate_template` + `result_refs`.

## Lawson aggregate manifest

`manifest.json` of the comfort result carries `gust_factor`: `{formula, floor: 1.0,
floor_applies_to: "cells_without_valid_ti", default_ti, resolved_ti_cells, default_ti_cells}`.
Cells without valid `ti` statistics (2D results, masked cells) use `default_ti`, whose
G = max(1, (1 + 3 I)/1.85) is the floor; resolved `ti` above (1.85 - 1)/3 = 0.283 lifts GEM above U.

## Output files (contract section 5)

Per heavy result: `manifest.json`, `fields/{K,ux,uy,[uz],speed,ti,mask}` (`section2d`:
`K, us, uz, speed, mask`), `fields.npz` (also holds `extent`), `scene.json` (the job's scene, for later maps),
`images/{k,speed,zones}.png` (150 dpi, names `k`, `speed`, `zones` in `results.images`),
and for `volume3d` also `images/slice_za.png` (K at z_a with streamlines) and
`images/slice_xz.png` (vertical cut along the wind), `volume/{slice_xz,slice_yz}.f32` +
`volume/viewer3d.json`. Plan maps are drawn bilinear with the exact building polygons on
top, facade elements (screens dashed, canopies hatched, fins dark, vegetation circles)
and a wind arrow "Viento desde φ°".
`images/delta.png` (name `delta`): after a heavy result is recorded, the heavy lane
looks for results of the project with the same `comparability_key`; an alternative
result gets ΔK = K - K_base against the newest base result (cmocean `balance`,
symmetric limits, ΔK < dk_reduction hatched and outlined), and a new base result
(re)renders it for every comparable alternative. "Base" is read from the api-owned
`alternatives.is_base` (read only; outside contract v1). Failures there are logged and
never fail the job.
Report PDF: per-study K maps with facade elements and wind arrow, plus "Comparación con
el caso base" when `baseline_study_id` is set: per direction, base | alternative maps on
one K scale, a ΔK map, a zone-area table (acceleration, stagnation, reduction, m² and %)
and a plain-Spanish conclusion ranking alternatives by acceleration area removed. Slice `extents` are
`[E_start, N_start, E_end, N_end, z_min, z_max]` (ENU metres). The manifest's
`convergence` carries both the contract section 6 keys and SOL-10's
`flow_throughs_spinup` / `flow_throughs_averaged`; `performance` is additive.
Aggregate: `fields/{lawson_class.u8, safety.u8, exceedance.f32}` (exceedance shape
`[n_comfort + n_safety, ny, nx]`), `images/lawson.png`.

## Validation and benchmarks

```bash
uv venv -p 3.12 .venv && uv pip install -p .venv -r requirements-dev.txt
.venv/bin/python -m pytest                  # unit + contract + coarse end-to-end
.venv/bin/python -m pytest -m integration   # real Postgres in Docker (kernel-assigned port)
.venv/bin/python -m pytest -m slow -s       # square cylinder (SOL-15), AIJ case A (SOL-16)
.venv/bin/python -m pytest -m bench         # benchmark runner smoke
.venv/bin/python -m app.services.bench.bench_runner [--device cpu|gpu]
```

GPU tests are marked `gpu` and skip with a reason when CuPy sees no device.

## Variables

See `.env.example`: `DATABASE_URL`, `DATA_DIR`, `RAFAGA_DEVICE`, `GPU_MEMORY_FRACTION`,
`CPU_MAX_NODES_3D`, `LIGHT_LANE_CONCURRENCY`, `LOG_LEVEL`, and worker timings
(`POLL_INTERVAL_S`, `HEARTBEAT_INTERVAL_S`, `ORPHAN_TIMEOUT_S`, `CANCEL_KILL_AFTER_S`,
`STARTUP_BENCHMARK`).

## Container

`docker build -t rafaga-solver services/solver` — python:3.12-slim, CuPy from
`cupy-cuda12x` plus only the `nvidia-cuda-runtime-cu12`, `nvidia-cuda-nvrtc-cu12` and `nvidia-cublas-cu12` wheels (not the full `[ctk]` extra; ~2.6 GB image instead of 5.5 GB), user 10001, `/data` owned by 10001, HEALTHCHECK on `/health`.
Without a GPU the image runs on NumPy; with `compose.gpu.yaml` it uses the GPU.
