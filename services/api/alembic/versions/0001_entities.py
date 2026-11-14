"""Core entities: users, projects, geometry, wind, alternatives, settings."""

from alembic import op

revision = "0001"
down_revision = None

DDL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email citext NOT NULL UNIQUE,
  password_hash text NOT NULL,
  role text NOT NULL CHECK (role IN ('architect','reviewer')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name text NOT NULL,
  lat double precision,
  lon double precision,
  elevation_m double precision,
  elevation_source text CHECK (elevation_source IN ('open_meteo','manual')),
  air_density_kg_m3 double precision,
  analysis_height_m real NOT NULL DEFAULT 1.5
    CHECK (analysis_height_m BETWEEN 0.5 AND 3.0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX projects_owner_idx ON projects (owner_id, updated_at DESC);

CREATE TABLE project_shares (
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (project_id, user_id)
);

CREATE TABLE geometries (
  project_id uuid PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  version integer NOT NULL DEFAULT 1,
  buildings jsonb NOT NULL DEFAULT '[]',
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE uploads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  kind text NOT NULL CHECK (kind IN ('geometry','background')),
  filename text NOT NULL,
  path text NOT NULL,
  size_bytes bigint NOT NULL,
  sha256 text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE background_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  upload_id uuid NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
  page_count integer NOT NULL DEFAULT 1,
  page integer NOT NULL DEFAULT 1,
  calibration jsonb,
  transform jsonb NOT NULL
    DEFAULT '{"offset":[0,0],"rotation_deg":0,"scale":1}',
  opacity real NOT NULL DEFAULT 0.5 CHECK (opacity BETWEEN 0 AND 1)
);

CREATE TABLE wind_climates (
  project_id uuid PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  source text NOT NULL DEFAULT 'manual' CHECK (source IN ('era5','manual')),
  period_years integer NOT NULL DEFAULT 10,
  rose jsonb,
  cache_key text,
  fetched_at timestamptz,
  manual_direction_deg real,
  manual_u10_ms real,
  terrain_category text NOT NULL DEFAULT 'urban',
  z0_m real NOT NULL DEFAULT 1.0,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE external_cache (
  kind text NOT NULL CHECK (kind IN ('geocode','elevation','era5')),
  key text NOT NULL,
  payload jsonb NOT NULL,
  fetched_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  PRIMARY KEY (kind, key)
);

CREATE TABLE alternatives (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name text NOT NULL,
  is_base boolean NOT NULL DEFAULT false,
  position integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX alternatives_one_base_idx
  ON alternatives (project_id) WHERE is_base;

CREATE TABLE facade_elements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  alternative_id uuid NOT NULL REFERENCES alternatives(id) ON DELETE CASCADE,
  building_id uuid NOT NULL,
  edge_index integer NOT NULL CHECK (edge_index >= 0),
  type text NOT NULL
    CHECK (type IN ('screen','fins','canopy','setback','vegetation')),
  params jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX facade_elements_alt_idx ON facade_elements (alternative_id);

CREATE TABLE user_settings (
  user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  thresholds jsonb NOT NULL,
  lawson jsonb NOT NULL,
  turbulence_intensity_default real NOT NULL,
  vegetation_cd real NOT NULL,
  alternatives_limit integer NOT NULL
);

CREATE TABLE templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
"""


def upgrade() -> None:
    """Create the core entity tables."""
    op.get_bind().exec_driver_sql(DDL)


def downgrade() -> None:
    """Drop the core entity tables."""
    for table in (
        "templates user_settings facade_elements alternatives external_cache "
        "wind_climates background_plans uploads geometries project_shares "
        "projects users"
    ).split():
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
