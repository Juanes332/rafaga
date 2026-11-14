"""Shared job-contract tables (contracts/job-contract.md section 2)."""

from alembic import op

revision = "0002"
down_revision = "0001"

DDL = """
CREATE TABLE studies (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id         uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  alternative_id     uuid NOT NULL REFERENCES alternatives(id) ON DELETE CASCADE,
  owner_id           uuid NOT NULL REFERENCES users(id),
  kind               text NOT NULL CHECK (kind IN ('plan2d','section2d','volume3d')),
  request            jsonb NOT NULL,
  dx_m               real NOT NULL,
  auto_coarsened     boolean NOT NULL DEFAULT false,
  aggregate_template jsonb,
  created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX studies_project_idx ON studies (project_id, created_at DESC);

CREATE TABLE jobs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id         uuid REFERENCES studies(id) ON DELETE CASCADE,
  project_id       uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  owner_id         uuid NOT NULL REFERENCES users(id),
  kind             text NOT NULL CHECK (kind IN
                   ('plan2d','section2d','volume3d','aggregate','render','report')),
  lane             text NOT NULL CHECK (lane IN ('heavy','light')),
  status           text NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued','running','completed','failed','cancelled')),
  priority         smallint NOT NULL DEFAULT 0,
  direction_deg    real,
  payload          jsonb NOT NULL,
  contract_version smallint NOT NULL DEFAULT 1,
  device_requested text NOT NULL DEFAULT 'auto'
                   CHECK (device_requested IN ('auto','cpu','gpu')),
  device_used      text CHECK (device_used IN ('cpu','gpu')),
  progress         real NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 1),
  phase            text CHECK (phase IN
                   ('preparing','spinup','averaging','postprocess','writing','rendering')),
  eta_seconds      integer,
  cancel_requested boolean NOT NULL DEFAULT false,
  resumable        boolean NOT NULL DEFAULT false,
  attempts         smallint NOT NULL DEFAULT 0,
  worker_id        text,
  error_code       text,
  error_message    text,
  error_details    jsonb,
  created_at       timestamptz NOT NULL DEFAULT now(),
  started_at       timestamptz,
  heartbeat_at     timestamptz,
  finished_at      timestamptz
);
CREATE INDEX jobs_queue_idx   ON jobs (lane, priority DESC, created_at) WHERE status = 'queued';
CREATE INDEX jobs_running_idx ON jobs (heartbeat_at) WHERE status = 'running';
CREATE INDEX jobs_study_idx   ON jobs (study_id);

CREATE FUNCTION notify_rafaga_jobs() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM pg_notify('rafaga_jobs', NEW.lane);
  RETURN NEW;
END $$;
CREATE TRIGGER jobs_notify AFTER INSERT OR UPDATE OF status ON jobs
  FOR EACH ROW WHEN (NEW.status = 'queued') EXECUTE FUNCTION notify_rafaga_jobs();

CREATE TABLE results (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id            uuid NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
  study_id          uuid NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
  project_id        uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  alternative_id    uuid NOT NULL REFERENCES alternatives(id) ON DELETE CASCADE,
  kind              text NOT NULL,
  direction_deg     real,
  dx_m              real NOT NULL,
  device            text NOT NULL,
  output_grid       jsonb NOT NULL,
  stats             jsonb NOT NULL,
  convergence       jsonb NOT NULL,
  comparability     jsonb NOT NULL,
  comparability_key text NOT NULL,
  dir               text NOT NULL,
  fields            jsonb NOT NULL,
  images            jsonb NOT NULL,
  warnings          jsonb NOT NULL DEFAULT '[]',
  created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX results_cmp_idx ON results (comparability_key);

CREATE TABLE comfort_results (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id     uuid NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
  job_id       uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  lawson_hash  text NOT NULL,
  lawson       jsonb NOT NULL,
  coverage     real NOT NULL,
  partial      boolean NOT NULL,
  class_areas  jsonb NOT NULL,
  safety_areas jsonb NOT NULL,
  dir          text NOT NULL,
  fields       jsonb NOT NULL,
  images       jsonb NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (study_id, lawson_hash)
);

CREATE TABLE exports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES users(id),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  layer text NOT NULL, params jsonb NOT NULL,
  file text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  owner_id uuid NOT NULL REFERENCES users(id),
  job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  version integer NOT NULL, params jsonb NOT NULL,
  file text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

CREATE TABLE solver_nodes (
  worker_id        text PRIMARY KEY,
  device           text NOT NULL CHECK (device IN ('cpu','gpu')),
  gpu_name         text,
  vram_total_bytes bigint,
  vram_free_bytes  bigint,
  ram_total_bytes  bigint NOT NULL,
  ram_budget_bytes bigint NOT NULL,
  cpu_cores        integer NOT NULL,
  mlups_2d         real,
  mlups_3d         real,
  solver_version   text NOT NULL,
  started_at       timestamptz NOT NULL,
  heartbeat_at     timestamptz NOT NULL
);

CREATE TABLE schema_meta (key text PRIMARY KEY, value text NOT NULL);
INSERT INTO schema_meta VALUES ('job_contract_version', '1');
"""


def upgrade() -> None:
    """Create the tables shared with the solver."""
    op.get_bind().exec_driver_sql(DDL)


def downgrade() -> None:
    """Drop the shared tables."""
    op.execute("DROP TRIGGER IF EXISTS jobs_notify ON jobs")
    op.execute("DROP FUNCTION IF EXISTS notify_rafaga_jobs()")
    for table in (
        "schema_meta solver_nodes reports exports comfort_results results "
        "jobs studies"
    ).split():
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
