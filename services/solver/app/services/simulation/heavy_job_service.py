"""Run one plan2d / section2d / volume3d job end to end (SOL-07..SOL-11, 19)."""

from collections.abc import Callable

from app.configs.config import SOLVER_VERSION, Settings
from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.device.array_module import to_host
from app.services.device.device_selector import select_device
from app.services.device.gpu_info import gpu_info
from app.services.device.host_resources import ram_budget, ram_total_and_available
from app.services.device.memory_guard import (
    BYTES_PER_NODE,
    OVERHEAD_BYTES,
    check_memory,
    cpu_node_cap,
    gpu_budget,
)
from app.services.lbm2d.lbm2d_case import build_plan_case, build_section_case
from app.services.lbm3d.lbm3d_case import build_volume_case
from app.services.postprocess.result_writer import write_result
from app.services.simulation.domain_rules import raised_top_payload, widened_payload
from app.services.simulation.simulation_runner import Reporter, SimulationRunner
from app.services.storage import output_dir_service as storage

_POST_PROGRESS = 0.99
_BUILDERS: dict[str, Callable] = {
    "plan2d": build_plan_case, "section2d": build_section_case, "volume3d": build_volume_case,
}


def _budget(device: str, dim: int, settings: Settings) -> tuple[int, int | None]:
    """Return the live memory budget (bytes) and node cap of a device."""
    if device == "gpu":
        info = gpu_info()
        return gpu_budget(info.total_bytes, info.free_bytes, settings.gpu_memory_fraction), None
    return ram_budget(), cpu_node_cap(dim, settings.cpu_max_nodes_3d, ram_total_and_available()[0])


def _fit_payload(p: HeavyPayload, device: str, settings: Settings) -> tuple[HeavyPayload, list[dict]]:
    """Raise a low 3D top within budget, then re-check memory (SOL-19)."""
    dim = 3 if p.job_kind == "volume3d" else 2
    budget, cap = _budget(device, dim, settings)
    per_node = p.memory.bytes_per_node or BYTES_PER_NODE[dim]
    room = max(budget - OVERHEAD_BYTES, 0) // per_node
    p, warnings = raised_top_payload(p, room if cap is None else min(room, cap))
    sim = widened_payload(p).grid.sim
    nodes = sim.nx * int(sim.ny or 1) * int(sim.nz or 1) if dim == 3 else sim.nx * int(sim.nz or sim.ny)
    check_memory(nodes, dim, sim.dx_m, budget, cap, p.memory.bytes_per_node)
    return p, warnings


def make_stepper(problem, device: str):
    """Return the GPU or CPU stepper for a problem."""
    if device == "gpu":
        from app.services.lattice.cuda_stepper import GpuStepper  # noqa: PLC0415

        return GpuStepper(problem)
    from app.services.lattice.numpy_stepper import CpuStepper  # noqa: PLC0415

    return CpuStepper(problem)


def run_heavy_job(raw: dict, job_id: str, settings: Settings, reporter: Reporter,
                  announce_device: Callable[[str], None] | None = None) -> dict:
    """Simulate, post-process and publish; return the result manifest."""
    payload = parse_payload(HeavyPayload, raw)
    device = select_device(payload.device, settings.rafaga_device, lambda: gpu_info() is not None)
    if announce_device:
        announce_device(device)
    payload, fit_warnings = _fit_payload(payload, device, settings)
    reporter(0.0, "preparing", None)
    case = _BUILDERS[payload.job_kind](payload)
    case.warnings.extend(fit_warnings)
    stepper = make_stepper(case.problem, device)
    try:
        outcome = SimulationRunner(case, stepper, reporter).run()
        reporter(_POST_PROGRESS, "postprocess", 0)
        avg_u, avg_u2 = to_host(stepper.avg_u), to_host(stepper.avg_u2)
    finally:
        stepper.close()
    final = storage.resolve(settings.data_dir, payload.output_dir)
    tmp = storage.temp_dir(final)
    shape = case.problem.shape
    manifest = write_result(case, avg_u.reshape((-1,) + shape), avg_u2.reshape(shape), outcome,
                            tmp, {"job_id": job_id, "device": device, "solver_version": SOLVER_VERSION})
    reporter(_POST_PROGRESS, "writing", 0)
    storage.publish(tmp, final)
    manifest["dir"] = payload.output_dir
    return manifest
