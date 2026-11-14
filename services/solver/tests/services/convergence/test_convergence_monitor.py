"""Tests for the ADR-11 convergence monitor."""

import numpy as np

from app.models.jobs.payload_schemas import ConvergenceParams
from app.services.convergence.convergence_monitor import ConvergenceMonitor

PARAMS = ConvergenceParams(spinup_ft=2, min_avg_ft=2, max_avg_ft=8, check_every_ft=0.25,
                           tolerance=0.01, consecutive=3)


def test_steady_field_converges_only_after_minimum_average() -> None:
    mon = ConvergenceMonitor(PARAMS, ft_steps=100)
    field = np.ones(10)
    stops = [mon.check(field, k * 25) for k in range(1, 9)]
    assert stops.index(True) == 7  # 8th check is the first at 200 averaged steps
    assert mon.converged and not mon.cap_reached


def test_changing_field_hits_cap_without_convergence() -> None:
    mon = ConvergenceMonitor(PARAMS, ft_steps=100)
    stop, k = False, 0
    while not stop:
        k += 1
        stop = mon.check(np.full(5, 1.0 + 0.1 * (k % 2)), k * 25)
    assert k * 25 == 800 and mon.cap_reached and not mon.converged
    report = mon.report(800)
    assert report["converged"] is False and report["flow_throughs_averaged"] == 8.0


def test_planned_steps_grow_but_never_pass_the_cap() -> None:
    mon = ConvergenceMonitor(PARAMS, ft_steps=100)
    assert mon.planned_steps(0) == 400
    assert mon.planned_steps(200) == 425
    assert mon.planned_steps(800) == 1000


def test_report_carries_contract_and_sol10_keys() -> None:
    mon = ConvergenceMonitor(PARAMS, ft_steps=100)
    mon.check(np.ones(3), 25)
    keys = set(mon.report(25))
    assert {"converged", "flow_throughs_spinup", "flow_throughs_averaged", "rel_change_last",
            "checks", "flow_through_steps", "cap_reached"} <= keys


def test_fixed_length_averages_to_the_cap_and_then_judges_convergence() -> None:
    mon = ConvergenceMonitor(PARAMS, ft_steps=100, fixed_length=True)
    stops = [mon.check(np.ones(4), k * 25) for k in range(1, 33)]
    assert stops.index(True) == 31  # only at 800 averaged steps (8 FT)
    assert mon.converged and not mon.cap_reached
    assert mon.planned_steps(0) == 1000
    assert mon.report(800)["averaging"] == "fixed"


def test_fixed_length_reports_honestly_when_the_mean_still_moves() -> None:
    mon = ConvergenceMonitor(PARAMS, ft_steps=100, fixed_length=True)
    for k in range(1, 33):
        mon.check(np.full(5, 1.0 + 0.1 * (k % 2)), k * 25)
    assert not mon.converged and mon.cap_reached
