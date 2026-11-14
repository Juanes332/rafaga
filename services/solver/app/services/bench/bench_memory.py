"""Peak device memory during a benchmark (CuPy pool sampling or host RSS)."""

import resource
import threading

from app.services.device.array_module import cupy_or_none


class PeakMemory:
    """Context manager sampling the CuPy pool every 20 ms (GPU) or RSS (CPU)."""

    def __init__(self, device: str) -> None:
        """Bind the device whose memory is tracked."""
        self.device = device
        self.peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def _now(self) -> int:
        """Return bytes in use right now."""
        if self.device == "gpu":
            return int(cupy_or_none().get_default_memory_pool().total_bytes())
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024

    def _sample(self) -> None:
        """Poll until stopped, keeping the maximum."""
        while not self._stop.wait(0.02):
            self.peak = max(self.peak, self._now())

    def __enter__(self) -> "PeakMemory":
        """Release cached blocks and start sampling."""
        if self.device == "gpu":
            cupy_or_none().get_default_memory_pool().free_all_blocks()
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        """Stop sampling and take a final reading."""
        self.peak = max(self.peak, self._now())
        self._stop.set()
        self._thread.join()
