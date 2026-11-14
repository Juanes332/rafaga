"""Skip marker for tests that need a CUDA GPU."""

import pytest

from app.services.device.array_module import cupy_or_none

HAS_GPU = cupy_or_none() is not None
requires_gpu = pytest.mark.skipif(not HAS_GPU, reason="no CUDA GPU visible to CuPy")
