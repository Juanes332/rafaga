"""The api-owned alternatives columns the solver relies on, pinned against the contract DDL (BL-09)."""

import re
from pathlib import Path

CONTRACT = Path(__file__).resolve().parents[5] / "docs/architecture/contracts/job-contract.md"
FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/db/job_contract.sql"


def _alternatives_ddl() -> str:
    """Return the CREATE TABLE alternatives statement of the DDL fixture."""
    match = re.search(r"CREATE TABLE alternatives\s*\((.*?)\);", FIXTURE.read_text(), re.S)
    assert match, "alternatives table missing from tests/fixtures/db/job_contract.sql"
    return match.group(1)


def test_alternatives_is_base_is_boolean_not_null() -> None:
    columns = {line.split()[0]: " ".join(line.split()[1:]).upper()
               for line in (c.strip() for c in _alternatives_ddl().split(",")) if line}
    assert columns["is_base"].startswith("BOOLEAN NOT NULL")


def test_contract_section_27_documents_is_base_as_boolean_not_null() -> None:
    text = CONTRACT.read_text()
    section = text[text.index("### 2.7"):]
    assert "`is_base` (`boolean NOT NULL`)" in section[:section.index("\n### ", 10)]


def test_contract_states_that_alternatives_project_id_is_not_read() -> None:
    text = CONTRACT.read_text()
    section = text[text.index("### 2.7"):]
    section = section[:section.index("\n### ", 10)]
    assert "`alternatives.project_id`" in section and "results.project_id" in section
