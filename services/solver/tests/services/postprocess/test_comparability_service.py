"""The comparability key must reproduce the contract example byte for byte."""

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.postprocess.comparability_service import comparability, comparability_key
from tests.support.contracts import example


def test_key_matches_result_manifest_example() -> None:
    payload = parse_payload(HeavyPayload, example("job.plan2d.example"))
    fields = comparability(payload)
    manifest = example("result-manifest.example")
    assert fields == manifest["comparability"]
    assert comparability_key(fields) == manifest["comparability_key"]


def test_key_changes_with_roughness() -> None:
    raw = example("job.plan2d.example")
    raw["wind"]["z0_m"] = 0.3
    other = comparability(parse_payload(HeavyPayload, raw))
    assert comparability_key(other) != example("result-manifest.example")["comparability_key"]
