"""cgroup-aware host resources."""

from pathlib import Path

from app.services.device.host_resources import cpu_cores, ram_total_and_available


def test_cgroup_memory_limit_caps_total(tmp_path: Path) -> None:
    (tmp_path / "memory.max").write_text("1073741824\n")
    (tmp_path / "memory.current").write_text("536870912\n")
    total, available = ram_total_and_available(tmp_path)
    assert total == 1073741824 and available <= 536870912


def test_cpu_quota_caps_cores(tmp_path: Path) -> None:
    (tmp_path / "cpu.max").write_text("200000 100000\n")
    assert cpu_cores(tmp_path) == 2


def test_unlimited_cgroup_keeps_host_values(tmp_path: Path) -> None:
    (tmp_path / "memory.max").write_text("max\n")
    total, _ = ram_total_and_available(tmp_path)
    assert total > 0 and cpu_cores(tmp_path) >= 1
