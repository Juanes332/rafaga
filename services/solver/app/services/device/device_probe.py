"""GPU probe for start scripts and the solver itself (ADR-17, SOL-03).

`python -m app.services.device.device_probe` prints one JSON line and
exits 0 only after a CuPy RawKernel ran on the GPU and returned the
right answer.
"""

import json
import sys

_KERNEL = r"""
extern "C" __global__ void vadd(const float* a, const float* b, float* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}
"""
_PROBE_BYTES = 64 * 1024 * 1024


def probe() -> dict:
    """Run the vector-add kernel; return facts or raise on any failure."""
    import cupy as cp  # noqa: PLC0415  (absence is a probe failure)

    if cp.cuda.runtime.getDeviceCount() < 1:
        raise RuntimeError("no CUDA device visible")
    n = _PROBE_BYTES // 4 // 2
    a = cp.arange(n, dtype=cp.float32)
    b = cp.full(n, 2.0, dtype=cp.float32)
    c = cp.empty_like(a)
    cp.RawKernel(_KERNEL, "vadd")(((n + 255) // 256,), (256,), (a, b, c, cp.int32(n)))
    if not bool(cp.allclose(c, a + 2.0)):
        raise RuntimeError("kernel returned a wrong result")
    props = cp.cuda.runtime.getDeviceProperties(0)
    name = props["name"].decode() if isinstance(props["name"], bytes) else str(props["name"])
    free, total = cp.cuda.runtime.memGetInfo()
    return {"ok": True, "gpu_name": name, "vram_total_bytes": int(total), "vram_free_bytes": int(free),
            "cuda_runtime": cp.cuda.runtime.runtimeGetVersion(),
            "driver": cp.cuda.runtime.driverGetVersion()}


def main() -> int:
    """Print the probe JSON and return the exit status."""
    try:
        print(json.dumps(probe()))
        return 0
    except Exception as exc:  # noqa: BLE001  (every failure is a "no GPU" answer)
        print(json.dumps({"ok": False, "gpu_name": None, "reason": f"{type(exc).__name__}: {exc}"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
