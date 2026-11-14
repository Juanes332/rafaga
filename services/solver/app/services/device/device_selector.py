"""Resolve the device of a job from the payload and RAFAGA_DEVICE (FR-56)."""

from collections.abc import Callable

from app.core.errors.solver_errors import DeviceUnavailableError


def select_device(job_device: str, setting: str, gpu_usable: Callable[[], bool]) -> str:
    """Return 'cpu' or 'gpu'; a forced GPU that is missing fails the job."""
    if setting == "cpu":
        if job_device == "gpu":
            raise DeviceUnavailableError("GPU disabled by RAFAGA_DEVICE=cpu", {"reason": "disabled"})
        return "cpu"
    wants_gpu = job_device == "gpu" or setting == "gpu"
    if gpu_usable():
        return "gpu" if job_device != "cpu" else "cpu"
    if wants_gpu and job_device != "cpu":
        raise DeviceUnavailableError("no usable CUDA GPU", {"reason": "not_detected"})
    return "cpu"
