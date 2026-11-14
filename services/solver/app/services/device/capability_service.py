"""Startup capabilities: device, memory and a <=5 s MLUPS benchmark (SOL-03)."""

import multiprocessing as mp
import time

from app.services.device.host_resources import cpu_cores, ram_budget, ram_total_and_available


def _mlups(stepper, seconds: float) -> float:
    """Return MLUPS of a stepper measured for about `seconds`."""
    stepper.step(2)
    sync = getattr(stepper, "synchronize", lambda: None)
    sync()
    steps, start = 0, time.perf_counter()
    while time.perf_counter() - start < seconds:
        stepper.step(10)
        sync()
        steps += 10
    rate = stepper.problem.nodes * steps / (time.perf_counter() - start) / 1e6
    stepper.close()
    return round(rate, 2)


def benchmark(device: str, budget_s: float = 4.0) -> dict:
    """Measure D2Q9 and D3Q19 throughput on the device within budget_s."""
    from app.services.simulation.heavy_job_service import make_stepper  # noqa: PLC0415
    from app.services.simulation.synthetic_problem import synthetic_problem  # noqa: PLC0415

    shape2, shape3 = ((300, 400), (64, 96, 160)) if device == "gpu" else ((150, 200), (24, 32, 64))
    return {"mlups_2d": _mlups(make_stepper(synthetic_problem(shape2), device), budget_s / 2),
            "mlups_3d": _mlups(make_stepper(synthetic_problem(shape3), device), budget_s / 2)}


def gather(setting: str, run_benchmark: bool) -> dict:
    """Return the solver_nodes capability fields (runs inside a child)."""
    from app.services.device.device_probe import probe  # noqa: PLC0415

    gpu = None
    if setting != "cpu":
        try:
            gpu = probe()
        except Exception:  # noqa: BLE001  (no GPU: fall back to CPU)
            gpu = None
    device = "gpu" if gpu else "cpu"
    total, _ = ram_total_and_available()
    caps = {"device": device, "gpu_name": gpu and gpu["gpu_name"],
            "vram_total_bytes": gpu and gpu["vram_total_bytes"],
            "vram_free_bytes": gpu and gpu["vram_free_bytes"], "ram_total_bytes": total,
            "ram_budget_bytes": ram_budget(), "cpu_cores": cpu_cores(),
            "mlups_2d": None, "mlups_3d": None}
    if run_benchmark:
        caps |= benchmark(device)
    return caps


def _child(setting: str, run_benchmark: bool, out) -> None:
    """Child entry: keep CUDA out of the supervisor process."""
    out.put(gather(setting, run_benchmark))


def detect(setting: str, run_benchmark: bool, timeout_s: float = 60.0) -> dict:
    """Return capabilities computed in a spawned process."""
    ctx = mp.get_context("spawn")
    out = ctx.Queue()
    proc = ctx.Process(target=_child, args=(setting, run_benchmark, out), daemon=True)
    proc.start()
    try:
        return out.get(timeout=timeout_s)
    finally:
        proc.join(5.0)
        if proc.is_alive():
            proc.kill()
