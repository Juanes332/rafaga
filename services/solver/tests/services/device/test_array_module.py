"""Tests for the array-module abstraction."""

import numpy as np
import pytest

from app.services.device.array_module import cupy_or_none, get_xp, to_host

requires_gpu = pytest.mark.skipif(cupy_or_none() is None, reason="no CUDA GPU visible")


def test_cpu_device_returns_numpy() -> None:
    assert get_xp("cpu") is np


@pytest.mark.gpu
@requires_gpu
def test_gpu_device_returns_cupy_and_round_trips() -> None:
    xp = get_xp("gpu")
    assert xp.__name__ == "cupy"
    assert to_host(xp.arange(3)).tolist() == [0, 1, 2]


def test_to_host_passes_numpy_through() -> None:
    a = np.zeros(2)
    assert to_host(a) is a
