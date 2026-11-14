# ADR-16 — Límites del respaldo en CPU y hardware mínimo (Q-6)

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Q-6 pregunta por el hardware mínimo recomendado en CPU y qué hacer en equipos con menos de 16 GB de RAM. Requisitos relacionados:

- **FR-38** y **BR-17:** respaldo automático en CPU.
- **NFR-03:** 3D en CPU con ≤3 M nodos en ≤90 min.
- **KPI-3:** 2D en CPU en ≤10 min.

Docker Desktop en WSL2 asigna por defecto el 50 % de la RAM del host a la VM.

## Decisión

### Requisitos de hardware publicados en el README

| Nivel | CPU | RAM disponible para Docker | Alcance |
|---|---|---|---|
| Mínimo | 4 núcleos | 8 GB | Solo 2D; el 3D se ofrece con un límite de 1,5 M nodos y un aviso |
| Recomendado sin GPU | 16 núcleos | 32 GB | 2D completo; 3D reducido (≤3 M nodos) |
| Recomendado con GPU | 8+ núcleos | 16 GB, más una GPU NVIDIA de 8 GB | Todo, incluido el 3D de hasta ~28 M nodos |

### Reglas del estimador en CPU (ADR-10)

- Presupuesto: `0,6 × MemAvailable` dentro del contenedor (respetando el límite del cgroup).
- En 3D: `nodes ≤ CPU_MAX_NODES_3D` (3e6 por defecto). Si la RAM visible es < 16 GB, el límite efectivo pasa a 1,5e6.
- Si el caso lo excede, el coarsening automático lleva dx hasta el límite. Si la resolución resultante incumple las 4 celdas mínimas, el trabajo se rechaza con una explicación que recomienda el 2D o una GPU.

### Avisos al lanzar

- Siempre se muestra el ETA en CPU, calculado con los MLUPS medidos en el arranque del `solver`.
- Si el ETA es > 30 min, la UI pide confirmación explícita («La simulación 3D en CPU tardará unos 75 min. ¿Lanzar?»).

### Ejecución

- Los hilos de NumPy se distribuyen por losas (ADR-03).
- El carril ligero se limita a `LIGHT_LANE_CONCURRENCY=2`, para que el render no compita con el carril pesado.

### README

Explica cómo subir la memoria de la VM WSL2 con `%UserProfile%\.wslconfig` (`[wsl2] memory=24GB`) y cómo reiniciarla (`wsl --shutdown`).

## Alternativas rechazadas

- **Sin límite en CPU.** Ejecuciones de varias horas sin aviso, posible swap y bloqueo del equipo.
- **Prohibir el 3D en CPU.** Contradice FR-38 y BR-17. El caso reducido sigue siendo útil para validar tendencias.
- **Detectar la RAM del host desde el script.** La RAM relevante es la de la VM de Docker, que solo se ve de forma fiable desde el contenedor.

## Consecuencias

Positivas:

- El comportamiento es predecible en equipos modestos y se explica antes de lanzar.

Negativas y riesgos:

- La resolución del 3D en CPU es baja, con avisos `low_resolution` y `low_reynolds` frecuentes. La UI recomienda usar el 3D en CPU solo como comprobación de tendencia.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** publica `ram_budget_bytes` y `cpu_cores` en `solver_nodes`.
- **WP-API:** aplica los límites en el estimador.
- **WP-WEB:** diálogo de confirmación por ETA largo.
- **WP-OPS:** tabla de hardware y `.wslconfig` en el README.
