"""PDF report job (SOL-14)."""

import copy
import time
from pathlib import Path

from pypdf import PdfReader

from app.services.report.report_service import run_report
from tests.support.contracts import example


def test_report_with_six_maps_is_fast_and_embeds_fonts(result_store, comfort_dir) -> None:
    raw = copy.deepcopy(example("job.report.example"))
    study = raw["snapshot"]["studies"][0]
    study["results"] = [{"result_dir": d, "wind_from_deg": w, "convergence": {"converged": False}}
                        for w, d in result_store.dirs.items()] * 2 + [
        {"result_dir": result_store.dirs[270.0], "wind_from_deg": 270.0, "convergence": {"converged": True}}]
    study["comfort_dir"] = comfort_dir
    start = time.perf_counter()
    rel = run_report(raw, result_store.settings)
    elapsed = time.perf_counter() - start
    path = Path(result_store.settings.data_dir) / rel
    assert path.read_bytes().startswith(b"%PDF") and elapsed <= 30
    reader = PdfReader(path)
    fonts = set()
    for page in reader.pages:
        for font in (page["/Resources"].get("/Font") or {}).values():
            desc = font.get_object()
            fonts.add(str(desc["/BaseFont"]))
            if "/DescendantFonts" in desc:
                desc = desc["/DescendantFonts"][0].get_object()
            embedded = desc["/FontDescriptor"].get_object()
            assert {"/FontFile2", "/FontFile3"} & set(embedded)
    assert any("Literata" in f for f in fonts) and any("Hanken" in f for f in fonts)
    footer = "no sustituye un ensayo"
    assert all(footer in page.extract_text() for page in reader.pages)
