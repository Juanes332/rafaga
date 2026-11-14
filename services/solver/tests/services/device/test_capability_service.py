"""Startup capabilities (SOL-03): RAFAGA_DEVICE=cpu forces NumPy."""

from app.services.device.capability_service import gather


def test_cpu_setting_reports_cpu_without_probing() -> None:
    caps = gather("cpu", run_benchmark=False)
    assert caps["device"] == "cpu" and caps["gpu_name"] is None
    assert caps["ram_budget_bytes"] > 0 and caps["cpu_cores"] >= 1


def test_benchmark_measures_mlups_on_cpu() -> None:
    from app.services.device.capability_service import benchmark

    result = benchmark("cpu", budget_s=0.6)
    assert result["mlups_2d"] > 0 and result["mlups_3d"] > 0
