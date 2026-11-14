"""Map any exception raised by a job to the contract's error triple."""

import logging

from app.core.errors.solver_errors import SolverError

logger = logging.getLogger(__name__)


def to_job_error(exc: BaseException) -> tuple[str, str, dict]:
    """Return (error_code, English message, details) for jobs.error_*."""
    if isinstance(exc, SolverError):
        return exc.code, exc.message, exc.details
    if isinstance(exc, OSError):
        return "io_error", "storage operation failed", {"path": getattr(exc, "filename", None)}
    if isinstance(exc, MemoryError):
        return "mesh_too_large", "out of memory while allocating the lattice", {}
    # The traceback stays in the log; the row gets a generic message.
    logger.error("job failed with an unexpected error", exc_info=exc)
    return "internal_error", "unexpected solver error", {}
