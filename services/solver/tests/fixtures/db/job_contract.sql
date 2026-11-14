-- Test-only schema: stub parents + the normative DDL of job-contract.md section 2
-- (extracted verbatim). Production schema is owned by the api's Alembic.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE TABLE users (id uuid PRIMARY KEY DEFAULT gen_random_uuid());
CREATE TABLE projects (id uuid PRIMARY KEY DEFAULT gen_random_uuid());
CREATE TABLE alternatives (id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  is_base boolean NOT NULL DEFAULT false);  -- api-owned; solver reads is_base (delta.png)
CREATE TABLE studies (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id         uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  alternative_id     uuid NOT NULL REFERENCES alternatives(id) ON DELETE CASCADE,
  owner_id           uuid NOT NULL REFERENCES users(id),
  kind               text NOT NULL CHECK (kind IN ('plan2d','section2d','volume3d')),
  request            jsonb NOT NULL,          -- body of POST /simulations as received
  dx_m               real NOT NULL,           -- resolved (after auto-coarsening)
  auto_coarsened     boolean NOT NULL DEFAULT false,
  aggregate_template jsonb,                   -- §3.4 without result_refs; NULL when wind source is manual
  created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX studies_project_idx ON studies (project_id, created_at DESC);

CREATE TABLE jobs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id         uuid REFERENCES studies(id) ON DELETE CASCADE,
  project_id       uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  owner_id         uuid NOT NULL REFERENCES users(id),
  kind             text NOT NULL CHECK (kind IN ('plan2d','section2d','volume3d','aggregate','render','report')),
  lane             text NOT NULL CHECK (lane IN ('heavy','light')),
  status           text NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued','running','completed','failed','cancelled')),
  priority         smallint NOT NULL DEFAULT 0,
  direction_deg    real,                       -- heavy 2D plan/3D jobs only
  payload          jsonb NOT NULL,             -- §3, self-contained
  contract_version smallint NOT NULL DEFAULT 1,
  device_requested text NOT NULL DEFAULT 'auto' CHECK (device_requested IN ('auto','cpu','gpu')),
  device_used      text CHECK (device_used IN ('cpu','gpu')),
  progress         real NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 1),
  phase            text CHECK (phase IN ('preparing','spinup','averaging','postprocess','writing','rendering')),
  eta_seconds      integer,
  cancel_requested boolean NOT NULL DEFAULT false,
  resumable        boolean NOT NULL DEFAULT false,
  attempts         smallint NOT NULL DEFAULT 0,
  worker_id        text,
  error_code       text,
  error_message    text,                       -- English, technical, never shown verbatim
  error_details    jsonb,                      -- structured hint data, e.g. {"proposed_dx_m": 1.5}
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
  output_grid       jsonb NOT NULL,            -- §3.2
  stats             jsonb NOT NULL,            -- {k_mean, k_max, k_p95, fluid_area_m2}
  convergence       jsonb NOT NULL,            -- §6
  comparability     jsonb NOT NULL,            -- the hashed fields, for diff listing (BR-11)
  comparability_key text NOT NULL,             -- sha256 hex of canonical JSON of `comparability`
  dir               text NOT NULL,             -- relative to /data
  fields            jsonb NOT NULL,            -- [{name, file, dtype, shape}]
  images            jsonb NOT NULL,            -- [{name, file}]
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
  coverage     real NOT NULL,                  -- simulated rose frequency / (1 - calm_fraction)
  partial      boolean NOT NULL,               -- coverage < 0.95 (BR-12)
  class_areas  jsonb NOT NULL,                 -- [{class, area_m2, percent}]
  safety_areas jsonb NOT NULL,                 -- [{label, area_m2, percent}]
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
  file text,                                    -- set by solver on completion
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
  worker_id        text PRIMARY KEY,           -- "<hostname>:<boot-uuid>"
  device           text NOT NULL CHECK (device IN ('cpu','gpu')),
  gpu_name         text,
  vram_total_bytes bigint,
  vram_free_bytes  bigint,
  ram_total_bytes  bigint NOT NULL,
  ram_budget_bytes bigint NOT NULL,            -- 0.6 * MemAvailable (cgroup-aware)
  cpu_cores        integer NOT NULL,
  mlups_2d         real,                       -- start-up micro-benchmark
  mlups_3d         real,
  solver_version   text NOT NULL,
  started_at       timestamptz NOT NULL,
  heartbeat_at     timestamptz NOT NULL
);
CREATE TABLE schema_meta (key text PRIMARY KEY, value text NOT NULL);
INSERT INTO schema_meta VALUES ('job_contract_version', '1');
