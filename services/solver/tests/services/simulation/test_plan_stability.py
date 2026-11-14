"""Regression: scenario plan2d at 22.5 deg diverged (wake vortex cores, Ma > 0.35)."""

import json
from pathlib import Path

import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.lbm2d.lbm2d_case import build_plan_case
from app.services.simulation.simulation_runner import SimulationRunner
from tests.support.gpu_marks import requires_gpu
from tests.support.scenario_factory import heavy_payload
from tests.support.stepper_choice import fastest

pytestmark = [pytest.mark.slow, pytest.mark.gpu, requires_gpu]
SCENE = Path(__file__).resolve().parents[2] / "fixtures" / "scenes" / "three_blocks_screen_canopy.json"
SCHEDULE = {"spinup_ft": 2.0, "min_avg_ft": 2.0, "max_avg_ft": 8.0, "check_every_ft": 0.25,
            "tolerance": 0.01, "consecutive": 3}


def test_live_scenario_plan_at_22_5_runs_without_mach_excursions() -> None:
    scene = json.loads(SCENE.read_text(encoding="utf-8"))
    case = build_plan_case(parse_payload(HeavyPayload, heavy_payload(scene, "plan2d", 22.5, 1.0, SCHEDULE)))
    stepper = fastest(case.problem)
    outcome = SimulationRunner(case, stepper, lambda *_: False).run()
    stepper.close()
    assert outcome.mach_spikes == 0
