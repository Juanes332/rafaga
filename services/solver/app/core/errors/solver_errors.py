"""Job failures with the error codes of job-contract.md section 4.1."""

from typing import Any


class SolverError(Exception):
    """Base for every job failure written to jobs.error_code."""

    code: str = "internal_error"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Keep the English technical message and structured hint data."""
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}


class MeshTooLargeError(SolverError):
    """The live device budget cannot hold the payload's lattice."""

    code = "mesh_too_large"


class DeviceUnavailableError(SolverError):
    """A GPU was forced but none is usable."""

    code = "device_unavailable"


class NumericalInstabilityError(SolverError):
    """NaN or local Mach above the configured guard."""

    code = "numerical_instability"


class InvalidPayloadError(SolverError):
    """The payload does not satisfy the job contract."""

    code = "invalid_payload"


class ContractVersionMismatchError(SolverError):
    """The payload speaks a contract version this solver does not know."""

    code = "contract_version_mismatch"


class StorageError(SolverError):
    """The data volume is full or a directory vanished."""

    code = "io_error"


class JobCancelledError(Exception):
    """Raised inside a job when cooperative cancellation was requested."""
