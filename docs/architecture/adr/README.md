# Registro de decisiones de arquitectura (ADR)

Decisiones de la Fase 2 de Ráfaga. Su fuente de verdad, en formato máquina, es `../plan.yaml` (`decisions`).

| Id | Título | Estado | Archivo |
|---|---|---|---|
| ADR-01 | Cuatro servicios de ejecución: api, solver, web y db | Aceptada | [ADR-01-four-runtime-services.md](ADR-01-four-runtime-services.md) |
| ADR-02 | Postgres como cola de trabajos | Aceptada | [ADR-02-postgres-job-queue.md](ADR-02-postgres-job-queue.md) |
| ADR-03 | Solver LBM único (D2Q9 / D3Q19) con LES y abstracción de dispositivo | Aceptada (enmendada por ADR-27) | [ADR-03-unified-lbm-solver.md](ADR-03-unified-lbm-solver.md) |
| ADR-04 | La api es dueña de la geometría y emite la escena canónica | Aceptada | [ADR-04-api-owns-geometry-scene.md](ADR-04-api-owns-geometry-scene.md) |
| ADR-05 | Descubrimiento de la api por la SPA: puertos persistidos y `config.json` en tiempo de ejecución | Aceptada | [ADR-05-spa-api-discovery-runtime-config.md](ADR-05-spa-api-discovery-runtime-config.md) |
| ADR-06 | Cuentas locales, JWT bearer y creación de cuenta en el primer arranque | Aceptada | [ADR-06-local-accounts-jwt.md](ADR-06-local-accounts-jwt.md) |
| ADR-07 | Progreso de trabajos por sondeo HTTP | Aceptada | [ADR-07-progress-polling.md](ADR-07-progress-polling.md) |
| ADR-08 | Datos externos de Open-Meteo a través de la api, con caché en Postgres | Aceptada | [ADR-08-open-meteo-via-api-cache.md](ADR-08-open-meteo-via-api-cache.md) |
| ADR-09 | Teselas de mapa: OSM raster a través de un proxy autenticado con caché en disco | Aceptada | [ADR-09-map-tiles-osm-proxy.md](ADR-09-map-tiles-osm-proxy.md) |
| ADR-10 | Estimador de memoria según VRAM/RAM y coarsening automático (Q-1) | Aceptada (enmendada por ADR-27) | [ADR-10-memory-estimator-auto-coarsening.md](ADR-10-memory-estimator-auto-coarsening.md) |
| ADR-11 | Criterio de convergencia y promediado temporal (Q-2) | Aceptada | [ADR-11-convergence-averaging.md](ADR-11-convergence-averaging.md) |
| ADR-12 | Condiciones de contorno y entrada de capa límite atmosférica (Q-3) | Aceptada (enmendada por ADR-27) | [ADR-12-boundary-conditions-abl.md](ADR-12-boundary-conditions-abl.md) |
| ADR-13 | Calibración de medios porosos: celosías, vegetación y elementos sub-celda (Q-3) | Aceptada | [ADR-13-porous-media-calibration.md](ADR-13-porous-media-calibration.md) |
| ADR-14 | Conversión de unidades LBM y estabilidad | Aceptada | [ADR-14-lbm-unit-conversion-stability.md](ADR-14-lbm-unit-conversion-stability.md) |
| ADR-15 | Confort Lawson LDDC: tabla por defecto y cálculo de excedencia (Q-5) | Aceptada | [ADR-15-lawson-lddc-comfort.md](ADR-15-lawson-lddc-comfort.md) |
| ADR-16 | Límites del respaldo en CPU y hardware mínimo (Q-6) | Aceptada | [ADR-16-cpu-fallback-limits.md](ADR-16-cpu-fallback-limits.md) |
| ADR-17 | Verificación de GPU en Linux y Windows/WSL2, y CuPy desde wheels (Q-7) | Aceptada (enmendada por ADR-29) | [ADR-17-gpu-verification-cupy-wheels.md](ADR-17-gpu-verification-cupy-wheels.md) |
| ADR-18 | Volumen de datos compartido y campos en float32 crudo | Aceptada | [ADR-18-shared-data-volume-raw-fields.md](ADR-18-shared-data-volume-raw-fields.md) |
| ADR-19 | El solver produce todos los artefactos numéricos; la api calcula áreas de zona | Aceptada | [ADR-19-solver-owns-numeric-artefacts.md](ADR-19-solver-owns-numeric-artefacts.md) |
| ADR-20 | Ley logarítmica desplazada para el perfil de viento | Aceptada | [ADR-20-shifted-log-law.md](ADR-20-shifted-log-law.md) |
| ADR-21 | Stack de frontend y sistema de diseño | Aceptada | [ADR-21-frontend-stack-design-system.md](ADR-21-frontend-stack-design-system.md) |
| ADR-22 | Modelo de procesos del solver: supervisor, carril pesado y carril ligero | Aceptada | [ADR-22-solver-process-model.md](ADR-22-solver-process-model.md) |
| ADR-23 | Comparabilidad: malla de salida común del proyecto y `comparability_key` | Aceptada | [ADR-23-comparability-common-output-grid.md](ADR-23-comparability-common-output-grid.md) |
| ADR-24 | Importadores de geometría: DXF, STL, OBJ e IFC hacia edificios con escalones | Aceptada | [ADR-24-geometry-importers.md](ADR-24-geometry-importers.md) |
| ADR-25 | Distribución: scripts start, stop y reset, secretos y enlace a loopback | Aceptada (enmendada por ADR-29) | [ADR-25-distribution-scripts.md](ADR-25-distribution-scripts.md) |
| ADR-26 | Valores de límite de peticiones | Aceptada | [ADR-26-rate-limits.md](ADR-26-rate-limits.md) |
| ADR-27 | Turbulencia 3D: LES con entrada sintética para recuperar las ráfagas resueltas (BL-01, BL-02) | Aceptada | [ADR-27-les-resolved-gusts.md](ADR-27-les-resolved-gusts.md) |
| ADR-28 | Capacidad del dispositivo del solver y aviso antes de un 3D en CPU (BL-06) | Aceptada | [ADR-28-device-capability-cpu-3d-warning.md](ADR-28-device-capability-cpu-3d-warning.md) |
| ADR-29 | Imagen del solver reducida y descarga opcional desde un registro (BL-05) | Aceptada | [ADR-29-solver-image-slimming-registry.md](ADR-29-solver-image-slimming-registry.md) |
