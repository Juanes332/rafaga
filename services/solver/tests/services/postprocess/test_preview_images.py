"""Previews registered in the manifest: plan maps and 3D slices (US-11, US-14)."""

import re
from pathlib import Path

import pytest

from app.configs.config import Settings
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support.payload_factory import plan_payload

NAME = re.compile(r"^(k|zones|speed|lawson|delta|slice_[a-z0-9_]+)\.png$")


@pytest.mark.parametrize("kind,dx,extra", [("plan2d", 6.0, set()),
                                           ("volume3d", 8.0, {"slice_za", "slice_xz"})])
def test_manifest_lists_previews_that_exist_and_match_the_contract(tmp_path: Path, kind, dx, extra) -> None:
    raw = plan_payload(dx=dx, kind=kind, device="cpu")
    manifest = run_heavy_job(raw, "j", Settings(data_dir=str(tmp_path)), lambda *_: False)
    names = {i["name"] for i in manifest["images"]}
    assert names == {"k", "speed", "zones"} | extra
    for image in manifest["images"]:
        assert NAME.match(Path(image["file"]).name)
        assert (tmp_path / manifest["dir"] / image["file"]).stat().st_size > 10_000


@pytest.mark.parametrize("nz,top_cells", [(18, 15), (12, 12)])
def test_vertical_slice_shows_five_heights_or_the_whole_domain(nz, top_cells) -> None:
    from app.models.jobs.payload_parser import parse_payload
    from app.models.jobs.payload_schemas import HeavyPayload
    from app.services.lbm3d.lbm3d_case import build_volume_case
    from app.services.postprocess.slice_images import section_window

    raw = plan_payload(dx=8.0, kind="volume3d", device="cpu")
    raw["grid"]["sim"]["nz"] = nz  # H = 24 m: 5 H = 15 cells
    case = build_volume_case(parse_payload(HeavyPayload, raw))
    _, _, z1 = section_window(case)
    assert z1 == top_cells
