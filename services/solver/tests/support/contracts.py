"""Load the normative contract examples used as fixtures."""

import json
from pathlib import Path

CONTRACTS = Path(__file__).resolve().parents[4] / "docs" / "architecture" / "contracts"


def example(name: str) -> dict:
    """Return contracts/examples/<name>.json as a dict."""
    return json.loads((CONTRACTS / "examples" / f"{name}.json").read_text(encoding="utf-8"))
