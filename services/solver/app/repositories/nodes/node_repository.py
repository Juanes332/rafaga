"""solver_nodes heartbeat upsert (job-contract.md 2.6)."""

from typing import Any

from psycopg import Connection

UPSERT_SQL = """
INSERT INTO solver_nodes (worker_id, device, gpu_name, vram_total_bytes, vram_free_bytes,
  ram_total_bytes, ram_budget_bytes, cpu_cores, mlups_2d, mlups_3d, solver_version,
  started_at, heartbeat_at)
VALUES (%(worker_id)s, %(device)s, %(gpu_name)s, %(vram_total_bytes)s, %(vram_free_bytes)s,
  %(ram_total_bytes)s, %(ram_budget_bytes)s, %(cpu_cores)s, %(mlups_2d)s, %(mlups_3d)s,
  %(solver_version)s, %(started_at)s, now())
ON CONFLICT (worker_id) DO UPDATE SET device = EXCLUDED.device, gpu_name = EXCLUDED.gpu_name,
  vram_total_bytes = EXCLUDED.vram_total_bytes, vram_free_bytes = EXCLUDED.vram_free_bytes,
  ram_total_bytes = EXCLUDED.ram_total_bytes, ram_budget_bytes = EXCLUDED.ram_budget_bytes,
  cpu_cores = EXCLUDED.cpu_cores, mlups_2d = EXCLUDED.mlups_2d, mlups_3d = EXCLUDED.mlups_3d,
  solver_version = EXCLUDED.solver_version, heartbeat_at = now();
"""


def upsert_node(conn: Connection, node: dict[str, Any]) -> None:
    """Insert or refresh this worker's capability row."""
    with conn.transaction():
        conn.execute(UPSERT_SQL, node)
        conn.execute("DELETE FROM solver_nodes WHERE heartbeat_at < now() - interval '1 day'")
