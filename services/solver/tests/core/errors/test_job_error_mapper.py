"""Exceptions map to contract error codes (job-contract 4.1)."""

from app.core.errors.job_error_mapper import to_job_error
from app.core.errors.solver_errors import MeshTooLargeError


def test_solver_errors_keep_code_and_details() -> None:
    assert to_job_error(MeshTooLargeError("m", {"proposed_dx_m": 1.5})) == (
        "mesh_too_large", "m", {"proposed_dx_m": 1.5})


def test_os_errors_are_io_errors() -> None:
    assert to_job_error(FileNotFoundError(2, "gone", "/data/x"))[0] == "io_error"


def test_unexpected_errors_leak_nothing() -> None:
    code, message, details = to_job_error(ValueError("postgres://secret@db"))
    assert code == "internal_error" and "secret" not in message and details == {}
