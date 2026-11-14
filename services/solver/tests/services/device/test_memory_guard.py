"""Tests for the SOL-19 memory guard (ADR-10 numbers)."""

import pytest

from app.core.errors.solver_errors import MeshTooLargeError
from app.services.device.memory_guard import check_memory, cpu_node_cap, gpu_budget

MIB = 1024 * 1024


def test_reference_gpu_budget_matches_adr10() -> None:
    assert gpu_budget(8188 * MIB, 8000 * MIB, 0.85) == int(0.85 * 8188 * MIB) - 512 * MIB


def test_25m_nodes_fit_the_reference_gpu() -> None:
    budget = gpu_budget(8188 * MIB, 8188 * MIB, 0.85)
    assert check_memory(25_000_000, 3, 1.0, budget) == 25_000_000 * 224 + 512 * MIB


def test_40m_nodes_propose_1_25_m() -> None:
    budget = gpu_budget(8188 * MIB, 8188 * MIB, 0.85)
    with pytest.raises(MeshTooLargeError) as err:
        check_memory(40_000_000, 3, 1.0, budget)
    assert err.value.details["proposed_dx_m"] == 1.25
    assert "1.25" in err.value.message


def test_cpu_3d_cap_lowered_on_small_hosts() -> None:
    assert cpu_node_cap(3, 3_000_000, 8 * 1024**3) == 1_500_000
    assert cpu_node_cap(2, 3_000_000, 8 * 1024**3) is None
    with pytest.raises(MeshTooLargeError):
        check_memory(4_000_000, 3, 1.0, 10**12, node_cap=3_000_000)
