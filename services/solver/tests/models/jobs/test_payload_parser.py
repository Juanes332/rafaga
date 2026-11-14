"""Contract tests: every normative example parses into its model."""

import pytest

from app.core.errors.solver_errors import ContractVersionMismatchError, InvalidPayloadError
from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import (
    AggregatePayload, HeavyPayload, RenderPayload, ReportPayload,
)
from tests.support.contracts import example


@pytest.mark.parametrize("name,model", [
    ("job.plan2d.example", HeavyPayload), ("job.volume3d.example", HeavyPayload),
    ("job.aggregate.example", AggregatePayload), ("job.render.example", RenderPayload),
    ("job.report.example", ReportPayload),
])
def test_contract_examples_parse(name, model) -> None:
    assert parse_payload(model, example(name)).contract_version == 1


def test_unknown_contract_version_is_rejected() -> None:
    raw = example("job.plan2d.example") | {"contract_version": 2}
    with pytest.raises(ContractVersionMismatchError) as err:
        parse_payload(HeavyPayload, raw)
    assert err.value.details == {"expected": 1, "got": 2}


def test_invalid_payload_reports_the_path() -> None:
    raw = example("job.plan2d.example")
    raw["grid"]["sim"]["dx_m"] = -1
    with pytest.raises(InvalidPayloadError) as err:
        parse_payload(HeavyPayload, raw)
    assert err.value.details["path"] == "grid.sim.dx_m"
