"""Pick the fastest available stepper for validation runs."""

from app.services.simulation.heavy_job_service import make_stepper
from tests.support.gpu_marks import HAS_GPU

DEVICE = "gpu" if HAS_GPU else "cpu"


def fastest(problem):
    """Return a GPU stepper when CuPy sees a GPU, else the CPU one."""
    return make_stepper(problem, DEVICE)
