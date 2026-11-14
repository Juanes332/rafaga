"""Tests for device resolution."""

import pytest

from app.core.errors.solver_errors import DeviceUnavailableError
from app.services.device.device_selector import select_device

YES, NO = (lambda: True), (lambda: False)


@pytest.mark.parametrize("job,setting,gpu,expected", [
    ("auto", "auto", YES, "gpu"), ("auto", "auto", NO, "cpu"), ("cpu", "auto", YES, "cpu"),
    ("auto", "cpu", YES, "cpu"), ("gpu", "auto", YES, "gpu"), ("auto", "gpu", YES, "gpu"),
])
def test_device_resolution(job, setting, gpu, expected) -> None:
    assert select_device(job, setting, gpu) == expected


@pytest.mark.parametrize("job,setting", [("gpu", "auto"), ("gpu", "cpu"), ("auto", "gpu")])
def test_forced_gpu_without_one_fails(job, setting) -> None:
    with pytest.raises(DeviceUnavailableError):
        select_device(job, setting, NO)
