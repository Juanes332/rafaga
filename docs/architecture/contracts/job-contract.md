# Contrato de trabajos api ↔ solver (v1.1)

Este documento es la interfaz entre **WP-API** y **WP-SOLVER**. Ninguno de los dos necesita
leer el código del otro: basta con respetar estas tablas, estas sentencias SQL, los
payloads y el formato de archivos del volumen. Versión del contrato: `job_contract_version = 1`
(en `schema_meta` y en cada `jobs.contract_version`). Revisión del documento: **v1.1**, aditiva
(§2.7: lecturas del solver sobre tablas del api); no cambia `job_contract_version`.

Ejemplos normativos (los dos WP los usan como fixtures de prueba):
`contracts/examples/scene.example.json`, `job.plan2d.example.json`,
`job.volume3d.example.json`, `job.aggregate.example.json`, `job.render.example.json`,
`job.report.example.json`, `result-manifest.example.json`.

---

## 1. Responsabilidades

| Tema | Dueño | El otro lado |
|---|---|---|
| Migraciones de **todas** las tablas (Alembic) | api | solver espera `schema_meta.job_contract_version = '1'` antes de reclamar trabajos (reintenta cada 5 s) |
| Escena canónica, malla de simulación y malla de salida | api (las resuelve y las congela en el payload) | solver las usa tal cual; nunca recalcula márgenes BR-16 |
| Encolar trabajos `plan2d`, `section2d`, `volume3d`, `render`, `report`, `aggregate` (recompute) | api | — |
| Encolar `aggregate` al terminar un estudio | solver (desde `studies.aggregate_template`) | api guarda la plantilla al crear el estudio |
| Ejecutar trabajos, progreso, cancelación efectiva, archivos de resultados, filas `results` / `comfort_results`, `exports.file`, `reports.file` | solver | api solo lee |
| Marcar cancelación (`cancel_requested`), cancelar trabajos en cola, reintentar | api | solver la respeta en ≤ 10 s |
| Capacidades del dispositivo (`solver_nodes`) | solver | api las lee para estimar (ADR-10) |
| Borrado de proyectos y sus directorios | api | solver tolera que un directorio desaparezca (falla el trabajo con `io_error`) |

Ambos contenedores montan el volumen con nombre `rafaga-data` en `/data` y corren como
uid/gid `10001`. Rutas guardadas en la BD son **relativas a `/data`**.

---

## 2. Tablas compartidas (DDL normativo)

Postgres ≥ 16. Extensiones: `pgcrypto` (gen_random_uuid), `citext`.

### 2.1 studies

```sql
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
```

El estado del estudio se **deriva** al leer (api): `queued` si todos en cola; `running` si
alguno corre; `completed` si todos completados; `partial` si terminados con ≥ 1 completado
y ≥ 1 fallido/cancelado; `failed` si todos fallaron; `cancelled` si todos cancelados.

### 2.2 jobs

```sql
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
```

Carriles: `plan2d`, `section2d`, `volume3d` → `heavy` (prioridad 0). `aggregate`, `render`,
`report` → `light` (prioridad 10). Límite de payload: 20 MB (api rechaza antes de insertar).

### 2.3 results (una fila por trabajo pesado completado)

```sql
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
```

`comparability` = `{kind, direction_deg, z0_m, uref_za_ms, dx_m, output_grid,
analysis_height_m, section}` (claves ordenadas, floats con 6 decimales, `section` null salvo
en cortes). `uref_za_ms` se calcula con U10 = 10 m/s fijo, así que solo cambia con z0 y z_a.

### 2.4 comfort_results

```sql
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
```

`lawson_hash` = sha256 del JSON canónico `{lawson, turbulence_intensity_default, rose_cache_key}`.

### 2.5 exports y reports

```sql
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
```

### 2.6 solver_nodes y schema_meta

```sql
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
```

Api considera el solver **en línea** si existe una fila con `heartbeat_at > now() - 30 s`
(usa la más reciente). El solver borra sus filas antiguas (`heartbeat_at < now() - 1 day`).

### 2.7 Lecturas del solver sobre tablas propiedad del api (v1.1, aditivo)

El solver **solo lee** las columnas listadas aquí de tablas cuyo dueño es el api; cualquier otra
columna o tabla del api queda fuera del contrato. Ampliar la lista es un cambio aditivo de este
documento y exige actualizar `API_OWNED_READS` en
`services/solver/app/repositories/results/result_repository.py` (un test lo fija).

| Tabla (dueño api) | Columnas que el solver puede leer | Semántica |
|---|---|---|
| `alternatives` | `id` | Clave de unión con `results.alternative_id` (FK ya definida en §2.3). |
| `alternatives` | `is_base` (`boolean NOT NULL`) | `true` marca la alternativa **caso base** del proyecto. El solver la usa tras cada resultado pesado (US-13) para elegir la base de `delta.png`: compara resultados con el mismo `comparability_key` (BR-11) del proyecto. Si el resultado nuevo es de la base, refresca el delta de las demás; si no, lo compara con el resultado base comparable más reciente. Sin fila base comparable no hay delta. El api garantiza a lo sumo una alternativa base por proyecto; si hubiera varias, el solver toma la del resultado más reciente. |

Reglas:

- Solo lectura: el solver nunca hace `INSERT`/`UPDATE`/`DELETE` sobre `alternatives`.
- `alternatives.project_id` **no se lee**: el proyecto de un resultado sale de `results.project_id`
  (§2.3), nunca de `alternatives`. Si el solver necesitara leerla, habría que añadirla a esta
  tabla y a `API_OWNED_READS` como cambio aditivo.
- La unión es `results r JOIN alternatives a ON a.id = r.alternative_id`; no usa `projects`,
  `users` ni otras columnas de `alternatives` (nombre, orden, escena).
- Las tablas `studies` (§2.1) y `schema_meta` (§2.6) que el solver también lee ya están
  definidas arriba; no forman parte de esta lista de lecturas adicionales.
- Cambiar el nombre, el tipo o la semántica de `is_base` es un cambio incompatible
  (sube `job_contract_version`, §7).

---

## 3. Payloads (`jobs.payload`)

Campos comunes a todo payload:

```json
{ "contract_version": 1, "job_kind": "plan2d", "project_id": "…", "output_dir": "results/<project_id>/<study_id>/<job_id>" }
```

`output_dir` es relativo a `/data`; el solver lo crea y escribe primero en
`<output_dir>.tmp/` y lo renombra al terminar (escritura atómica).

### 3.1 Convención de dirección y marco de simulación

- Dirección meteorológica `wind_from_deg` φ: de dónde **viene** el viento, grados horarios
  desde el norte. Sectores: 16 centrados en 0, 22.5, …, 337.5 (sector i cubre
  [22.5 i − 11.25, 22.5 i + 11.25)).
- Vector de avance (hacia dónde va el flujo): **d** = (−sin φ, −cos φ) en ENU.
  Eje y del marco de simulación: **n** = (cos φ, −sin φ) (d girado +90°).
- Un punto ENU p pasa al marco de simulación como `x_s = p·d`, `y_s = p·n`, `z_s = z`.
  El flujo entra por `x_s` mínimo (cara de entrada) y sale por `x_s` máximo.

### 3.2 Mallas

```json
"grid": {
  "sim": {
    "frame": "wind",                      // "section" for section2d
    "wind_from_deg": 270.0,
    "axis_x": [1.0, 0.0], "axis_y": [0.0, 1.0],   // d and n in ENU, informative
    "origin": [-140.0, -145.0, 0.0],      // lower corner, sim-frame metres
    "dx_m": 1.0,
    "nx": 520, "ny": 290, "nz": null      // nz only for volume3d
  },
  "output": { "frame": "plan", "origin_x": -68.0, "origin_y": -73.0, "dx_m": 1.0, "nx": 136, "ny": 146 }
}
```

Reglas (las aplica **api**; el solver las da por buenas):

1. `H = scene.h_max_m`; caja base = `scene.bounds` (edificios base) ampliada en
   `envelope_m = 10` por lado en planta.
2. Malla `sim`: proyectar las 4 esquinas de la caja al marco de simulación; `x0 = xmin − 5H`,
   `x1 = xmax + 15H`, `y0 = ymin − 5H`, `y1 = ymax + 5H`; 3D: `z1 = 5H` (BL-02: cabe 25 M nodos en 8 GB; el 2D/sección conserva 6H), y si el bloqueo
   (área frontal de la caja base / (Ly·Lz)) ≥ 3 % se amplían Ly y Lz con el mismo factor
   hasta < 3 %. `nx = ceil((x1−x0)/dx)`, etc. Centros de celda en `origin + (i + 0.5)·dx`.
3. Malla `output` en planta (común a todas las direcciones y alternativas del proyecto
   con el mismo `dx`): caja base ampliada en `envelope_m + 2H`, alineada a múltiplos de
   `dx`, norte arriba. Arreglos fila-mayor con forma `(ny, nx)`; **fila 0 = sur**, columna
   0 = oeste. Valor de celda en el centro `(origin_x + (i+0.5)dx, origin_y + (j+0.5)dx)`.
4. `section2d`: `frame: "section"`, eje s a lo largo de p0→p1 (el usuario traza de barlovento
   a sotavento; `wind_from_deg` = rumbo de p1→p0), `origin: [s0, 0]` con `s0 = −5H`,
   `ns = ceil((|p1−p0| + 20H)/dx)`, `nz = ceil(6H/dx)`. Salida `{"frame":"section","s0","dx_m","ns","nz"}`,
   forma `(nz, ns)`, fila 0 = suelo.
5. Muestreo de la salida desde la malla `sim` rotada: bilineal (2D) / trilineal (3D en z_a);
   celdas sólidas → NaN en K y velocidades, `mask = 1`.

### 3.3 `plan2d`, `section2d`, `volume3d` (carril heavy)

```json
{
  "contract_version": 1,
  "job_kind": "volume3d",
  "project_id": "…", "study_id": "…", "alternative_id": "…",
  "output_dir": "results/<p>/<s>/<j>",
  "scene": { "…": "contracts/scene.schema.json" },
  "section": null,                                   // {"p0":[x,y],"p1":[x,y]} for section2d
  "wind": {
    "wind_from_deg": 270.0,
    "u10_ms": 10.0,                                  // nominal; K is scale-free (ADR-14)
    "z0_m": 1.0,
    "analysis_height_m": 1.5,
    "ustar_ms": 1.7098,                              // κ U10 / ln((10+z0)/z0)
    "uref_za_ms": 3.8212,                            // (u*/κ) ln((z_a+z0)/z0)  (ADR-20)
    "air_density_kg_m3": 1.2,
    "kappa": 0.41
  },
  "grid": { "sim": { "…": "§3.2" }, "output": { "…": "§3.2" } },
  "physics": {
    "u_lattice_ref": 0.05,
    "nu_lattice_floor": 5e-5,
    "smagorinsky_cs": 0.17,
    "tau_min": 0.5005, "tau_max": 2.0,
    "collision": "regularized_bgk",
    "sponge_fraction": 0.10, "sponge_tau": 1.0,
    "inflow_perturbation": 0.02,                     // 3D only; seeded
    "seed": 12345,
    "max_local_mach": 0.35,
    "subgrid_coverage_solid": 0.5,
    "supersampling": 4
  },
  "convergence": {
    "spinup_ft": 1.5, "min_avg_ft": 2.0, "max_avg_ft": 6.0,      // 2D: 2.0 / 2.0 / 8.0
    "check_every_ft": 0.25, "tolerance": 0.01, "consecutive": 3
  },
  "device": "auto",
  "memory": { "estimate_bytes": 5401075712, "bytes_per_node": 224, "overhead_bytes": 536870912 },
  "render": { "dpi": 150, "k_accel": 1.2, "k_stagnation": 0.3 }
}
```

Notas físicas (implementación en solver, decisión en ADR-11..ADR-14):

- Entrada: 2D planta = uniforme `u_lat`; corte y 3D = ley log desplazada escalada para que
  `u(z_top) = u_lattice_ref`. K = |U| / U_ref(z_a), con U_ref(z_a) del perfil de entrada.
- Suelo (corte, 3D): bounce-back a media celda + fuerza de pared log en la primera capa.
  Techo y laterales: deslizamiento libre. Salida: ρ = 1 regularizada + esponja.
- 2D planta: solo primitivas con `z_min ≤ z_a ≤ z_max` (las demás generan aviso
  `below_analysis_height` / se ignoran, p. ej. marquesinas por encima de z_a).

### 3.4 `aggregate` (carril light)

```json
{
  "contract_version": 1, "job_kind": "aggregate", "project_id": "…", "study_id": "…",
  "output_dir": "results/<p>/<s>/aggregate-<lawson_hash[:12]>",
  "lawson_hash": "…",
  "result_refs": [ { "result_id": "…", "wind_from_deg": 270.0, "dir": "results/<p>/<s>/<j>" } ],
  "rose": { "cache_key": "…", "calm_fraction": 0.04,
            "sectors": [ { "center_deg": 0.0, "frequency": 0.05, "weibull_k": 1.9, "weibull_c_ms": 4.1 } ] },
  "site": { "z0_m": 1.0, "z0_ref_m": 0.03, "blending_height_m": 60.0, "analysis_height_m": 1.5 },
  "lawson": {
    "exceedance": 0.05,
    "comfort": [ { "class": "A", "key": "sitting", "threshold_ms": 4.0 },
                 { "class": "B", "key": "standing", "threshold_ms": 6.0 },
                 { "class": "C", "key": "strolling", "threshold_ms": 8.0 },
                 { "class": "D", "key": "business_walking", "threshold_ms": 10.0 } ],
    "uncomfortable_class": "E",
    "safety": [ { "key": "frail_cyclists", "threshold_ms": 15.0, "exceedance": 0.00025 },
                { "key": "general_public", "threshold_ms": 20.0, "exceedance": 0.00025 } ]
  },
  "turbulence_intensity_default": 0.25,
  "output_grid": { "…": "§3.2" }
}
```

Cálculo por celda (ADR-15): `T = [ln((z_a+z0)/z0) / ln(h_b/z0)] · [ln(h_b/z0_ref) / ln((10+z0_ref)/z0_ref)]`;
`G = max(1, (1 + 3 I)/1.85)` con I de `ti` del resultado (3D) o `turbulence_intensity_default` (2D);
`P(U > U_t) = Σ_d f_d · exp(−(U_t / (G·K_d·T·c_d))^{k_d}) / coverage`, con d los sectores
simulados (cada resultado se asigna al sector que contiene su `wind_from_deg`; si un sector
tiene varios resultados se promedia K). Clase = primera de A..D cuya P ≤ `exceedance`; si
ninguna, E. Seguridad: celda marcada si P(U > umbral) > exceedance de seguridad.
Cobertura = Σ f_d simulados / (1 − calm_fraction). `partial = coverage < 0.95`.

Al terminar el **último** trabajo pesado de un estudio (cualquier estado terminal), el
solver, en la misma transacción y con `SELECT … FROM studies WHERE id = $1 FOR UPDATE`,
inserta un `aggregate` a partir de `studies.aggregate_template` + `result_refs` si
`aggregate_template IS NOT NULL`, existe ≥ 1 resultado y no hay ya un `aggregate` con el
mismo `lawson_hash` en estado `queued|running|completed`. La api inserta `aggregate`
directamente en `POST /simulations/{id}/comfort/recompute`.

### 3.5 `render` (carril light)

```json
{
  "contract_version": 1, "job_kind": "render", "project_id": "…",
  "export_id": "…", "output_dir": "exports/<owner_id>",
  "file_name": "<export_id>.png",
  "layer": "delta_k",                               // k | zones | speed | delta_k | lawson
  "result_dir": "results/<p>/<s>/<j>",
  "compare_result_dir": "results/<p>/<s2>/<j2>",    // delta_k (and zones with reduction) only
  "comfort_dir": null,                              // lawson only
  "output_grid": { "…": "§3.2" },
  "thresholds": { "k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1 },
  "dpi": 300,
  "labels": { "project_name": "…", "alternative_a": "Caso base", "alternative_b": "Celosía 40 %",
              "wind": "Viento del 270° (O), U10 = 10,0 m/s", "disclaimer": "Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento." },
  "scene": { "…": "scene.schema.json, for building outlines" }
}
```

El PNG lleva leyenda numérica con unidades, barra de escala, flecha de norte, viento de
referencia y el aviso; metadatos pHYs = dpi. Al terminar, el solver hace
`UPDATE exports SET file = '<output_dir>/<file_name>'`.

### 3.6 `report` (carril light)

```json
{
  "contract_version": 1, "job_kind": "report", "project_id": "…",
  "report_id": "…", "version": 3, "output_dir": "reports/<project_id>",
  "file_name": "rafaga-<slug>-v3.pdf",
  "snapshot": {
    "project": { "name": "…", "lat": 0.0, "lon": 0.0, "elevation_m": 0.0, "elevation_source": "manual",
                 "air_density_kg_m3": 1.225, "analysis_height_m": 1.5 },
    "wind": { "source": "era5", "period_years": 10, "terrain_category": "urban", "z0_m": 1.0,
              "rose": { "…": "WindRose" } },
    "studies": [ { "study_id": "…", "alternative_name": "…", "kind": "plan2d", "dx_m": 1.0,
                   "device": "gpu", "results": [ { "result_dir": "…", "wind_from_deg": 270.0,
                   "convergence": { "converged": true } } ],
                   "zone_areas": { "…": "ZoneAreas" }, "comfort_dir": "…|null",
                   "comfort_areas": { "…": "Comfort" } } ],
    "baseline_study_id": "…",
    "thresholds": { "k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1 },
    "lawson": { "…": "§3.4" },
    "generated_at": "2026-01-01T00:00:00Z",
    "app_version": "1.0.0",
    "disclaimer": "Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento."
  }
}
```

(Los valores de ubicación del ejemplo son marcadores sintéticos; en ejecución vienen del
proyecto. Nunca hay valores por defecto de ubicación.)

---

## 4. Ciclo de vida y SQL normativo

```
queued ──claim──▶ running ──ok──────────▶ completed
   │                 ├──error────────────▶ failed (resumable=false)
   │                 ├──cancel_requested─▶ cancelled
   │                 └──worker died──────▶ failed (resumable=true, worker_restarted)
   └──api cancel─────────────────────────▶ cancelled
failed(resumable) ──api retry──▶ queued
```

**Reclamar** (solver, una transacción, por carril):

```sql
UPDATE jobs SET status = 'running', worker_id = $1, started_at = now(),
               heartbeat_at = now(), attempts = attempts + 1, phase = 'preparing'
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'queued' AND lane = $2 AND NOT cancel_requested
  ORDER BY priority DESC, created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1)
RETURNING *;
```

Despertar: `LISTEN rafaga_jobs` (payload = carril) y sondeo cada 2 s como respaldo.
Concurrencia: heavy = 1 trabajo a la vez por solver; light = `LIGHT_LANE_CONCURRENCY` (2).

**Progreso** (solver, como máximo 1 vez/s, al menos cada 2 s mientras corre):

```sql
UPDATE jobs SET progress = $2, phase = $3, eta_seconds = $4, heartbeat_at = now()
WHERE id = $1 AND status = 'running'
RETURNING cancel_requested;
```

`progress` = pasos hechos / pasos previstos, donde previstos = `(spinup_ft + min_avg_ft)·FT`
hasta que el monitor de convergencia extiende el promediado (entonces se recalcula con el
siguiente múltiplo de `check_every_ft`, sin pasar nunca de `max_avg_ft`); `progress` nunca
disminuye. `eta_seconds` = pasos restantes × nodos / MLUPS medidos.

**Cancelar** (api): `UPDATE jobs SET status='cancelled', finished_at=now() WHERE id=$1 AND status='queued'`;
si corre: `UPDATE jobs SET cancel_requested = true WHERE id=$1 AND status='running'`.
El solver lo detecta en la siguiente actualización de progreso (≤ 1 s), pide al proceso hijo
que pare, lo mata a los 8 s, borra `<output_dir>.tmp/` y escribe
`status='cancelled', finished_at=now()`. Total ≤ 10 s.

**Completar** (solver, una transacción): insertar fila `results` (o `comfort_results`, o
fijar `exports.file` / `reports.file`), luego
`UPDATE jobs SET status='completed', progress=1, phase=NULL, eta_seconds=0, finished_at=now()`,
luego la regla de §3.4 para `aggregate`.

**Fallar**: `status='failed', error_code, error_message, error_details, finished_at=now()`;
directorio temporal borrado.

**Recuperación al arrancar** (solver): 
`UPDATE jobs SET status='failed', resumable=true, error_code='worker_restarted', finished_at=now()
WHERE status='running' AND heartbeat_at < now() - interval '60 seconds'`.

**Reintentar** (api): `UPDATE jobs SET status='queued', resumable=false, error_code=NULL,
error_message=NULL, error_details=NULL, progress=0, phase=NULL, cancel_requested=false,
worker_id=NULL WHERE id=$1 AND status='failed' AND resumable`.

### 4.1 Códigos de error del solver

| error_code | Cuándo | error_details |
|---|---|---|
| `mesh_too_large` | presupuesto real del dispositivo < memoria necesaria (SOL-19) | `{needed_bytes, budget_bytes, proposed_dx_m}` |
| `device_unavailable` | `device = gpu` forzado y no hay GPU usable | `{reason}` |
| `numerical_instability` | NaN o Mach local > `max_local_mach` | `{step, max_mach}` |
| `invalid_payload` | payload no cumple el contrato | `{path, reason}` |
| `contract_version_mismatch` | `contract_version` ≠ 1 | `{expected, got}` |
| `io_error` | volumen lleno, directorio borrado | `{path}` |
| `worker_restarted` | recuperación al arrancar | `{}` |
| `internal_error` | cualquier otra excepción (mensaje genérico, traza solo en logs) | `{}` |

La SPA traduce `error_code` a texto es-CO con causa y solución; nunca muestra `error_message`.

---

## 5. Volumen `/data` y formatos de archivo

```
/data
├── uploads/<project_id>/<upload_id>.<ext>                 api
├── cache/tiles/<z>/<x>/<y>.png                            api
├── results/<project_id>/<study_id>/<job_id>/              solver
│   ├── manifest.json
│   ├── fields/K.f32  ux.f32  uy.f32  [uz.f32]  speed.f32  ti.f32  mask.u8
│   ├── fields.npz                                         (all fields + grid, for download)
│   ├── images/k.png  speed.png  zones.png
│   ├── volume/                                            (volume3d only)
│   │   ├── slice_xz.f32  slice_yz.f32                     (speed on vertical mid-planes)
│   │   └── viewer3d.json
│   └── log.jsonl
├── results/<project_id>/<study_id>/aggregate-<hash12>/
│   ├── manifest.json  fields/lawson_class.u8  fields/exceedance.f32  images/lawson.png
├── exports/<owner_id>/<export_id>.png                     solver
└── reports/<project_id>/rafaga-<slug>-v<n>.pdf            solver
```

- `.f32`: float32 little-endian, fila-mayor, sin cabecera; forma en `manifest.json` y en
  `results.fields`. NaN en celdas sólidas. `.u8`: uint8 (mask: 0 fluido, 1 sólido,
  2 poroso; lawson_class: 0..4 = A..E, 255 = sólido).
- Campos en planta en la malla `output` (§3.2); `section2d` usa `us` (a lo largo de s) y `uz`
  en lugar de `ux`/`uy`.
- `ti` = intensidad de turbulencia resuelta σ_u/|U| (3D) o NaN en 2D.
- `viewer3d.json`: `{"slices":[{"name":"xz","plane":{"axis":"y","value_m":…},"extents":[…],"field":"slice_xz","shape":[nz,nx]}],"streamlines":[[[x,y,z],…]],"frame":"local_enu"}`
  (coordenadas ya en ENU; ≤ 400 líneas de corriente de ≤ 500 puntos).
- `manifest.json`: ver `examples/result-manifest.example.json`; contiene exactamente lo que
  va a la fila `results` más `contract_version` y `solver_version`.

La api expone cada archivo solo por nombre lógico permitido (allow-list), nunca por ruta.

## 6. Convergencia (`results.convergence`)

```json
{ "converged": true, "flow_through_steps": 10400, "spinup_ft": 1.5,
  "averaged_ft": 2.75, "checks": 11, "rel_change_last": 0.0071, "mean_speed_change_last": 0.0043,
  "cap_reached": false }
```

## 7. Compatibilidad y evolución

Cambios aditivos (campos nuevos opcionales) no suben la versión. Cualquier cambio de
semántica o de campos obligatorios sube `job_contract_version` a 2 en `schema_meta`, en los
payloads y en este documento; el solver rechaza versiones que no conoce con
`contract_version_mismatch`.
