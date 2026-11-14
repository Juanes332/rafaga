"""Pin the api-owned columns the solver reads (job contract v1.1, section 2.7)."""

import re
from pathlib import Path

from app.repositories.results import result_repository as results

APP = Path(__file__).resolve().parents[3] / "app"
# Table -> columns the solver may read from api-owned tables.
EXPECTED_API_READS = {"alternatives": {"id", "is_base"}}


def _columns_of(sql: str, table: str) -> set[str]:
    """Return the columns of `table` referenced in `sql` through its alias."""
    alias = re.search(rf"\b{table}\s+(\w+)\b", sql).group(1)
    return set(re.findall(rf"\b{alias}\.(\w+)", sql))


def test_comparable_results_reads_only_the_documented_alternatives_columns() -> None:
    sql = results.COMPARABLE_RESULTS_SQL
    assert _columns_of(sql, "alternatives") == EXPECTED_API_READS["alternatives"]


def test_declared_api_reads_match_the_expected_pin() -> None:
    assert results.API_OWNED_READS == EXPECTED_API_READS


def test_no_other_repository_touches_the_alternatives_table() -> None:
    offenders = [str(p.relative_to(APP)) for p in APP.rglob("*.py")
                 if re.search(r"\b(FROM|JOIN|UPDATE|INTO)\s+alternatives\b", p.read_text())
                 and p.name != "result_repository.py"]
    assert offenders == []


CONTRACT = Path(__file__).resolve().parents[5] / "docs/architecture/contracts/job-contract.md"
_ROW = re.compile(r"^\|\s*`(\w+)`(?:\s*\(.*?\))?\s*\|\s*`(\w+)`")


def _documented_reads() -> dict[str, set[str]]:
    """Parse the section 2.7 table of the job contract into {table: columns}."""
    text = CONTRACT.read_text(encoding="utf-8")
    section = text.split("### 2.7", 1)[1].split("\n### ", 1)[0].split("\n---", 1)[0]
    reads: dict[str, set[str]] = {}
    for line in section.splitlines():
        match = _ROW.match(line)
        if match:
            reads.setdefault(match.group(1), set()).add(match.group(2))
    return reads


def test_contract_section_2_7_table_matches_declared_and_sql_reads() -> None:
    """Documentation drift fails: doc table == API_OWNED_READS == SQL columns."""
    documented = _documented_reads()
    assert documented == results.API_OWNED_READS
    assert _columns_of(results.COMPARABLE_RESULTS_SQL, "alternatives") == documented["alternatives"]
