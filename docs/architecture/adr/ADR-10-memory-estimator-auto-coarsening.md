# ADR-10 — Estimador de memoria según VRAM/RAM y coarsening automático (Q-1)

Estado: Aceptada
Fecha: 2026-11-13

> Enmienda (2026-11-13, ADR-27): en `volume3d` el techo del dominio pasa de 6H a 5H, manteniendo el bloqueo < 3 %. Los ejemplos de esta ADR siguen siendo válidos como cota superior.

## Contexto

Q-1 pide una estrategia de coarsening automático cuando la VRAM no alcanza (supuesto A-8). Requisitos relacionados:

- **FR-40:** estimar la memoria antes de lanzar y, si no cabe, rechazar o proponer coarsening.
- **US-09:** un caso demasiado grande se rechaza con la sugerencia de aumentar la celda.
- **US-10:** con 8 GB caben ≈28 M nodos; si se excede, se propone coarsening o se rechaza con explicación.
- **NFR-02:** 25 M nodos deben caber en ≤7,2 GB.
- **C-4** y **BR-16**.

## Decisión

### Constantes del contrato

Se usan en la `api` para estimar y en el `solver` para la comprobación final (SOL-19).

| Retícula | Bytes por nodo | Composición |
|---|---|---|
| D2Q9 | 104 B | 2×9×4 (dos buffers) + 6×4 (ρ, u, medias, sumas de cuadrados) + 8 (máscara, id poroso, relleno) |
| D3Q19 | 224 B | 2×19×4 (dos buffers) + 16×4 (ρ, u, medias, segundos momentos, ν_t, fuerza) + 8 (máscara, id poroso) |

A eso se suma una sobrecarga fija de `512 MiB` (contexto CUDA, kernels compilados y pool de CuPy).

`need = nodes × bytes_per_node + 512 MiB`

### Presupuesto por dispositivo

Los valores salen de la última fila de `solver_nodes` (ADR-22):

- **GPU:** `budget = GPU_MEMORY_FRACTION(0.85) × vram_total − 512 MiB`. Esos 512 MiB se reservan para el escritorio y el driver en WSL2.
- **CPU:** `budget = 0.6 × MemAvailable`. MemAvailable se lee respetando el límite del cgroup del contenedor. Además, en 3D se aplica `nodes ≤ CPU_MAX_NODES_3D` (3e6) (ADR-16).

### Ejemplo con la máquina de referencia (RTX 4060, 8188 MiB)

- `budget = 0.85 × 8188 MiB − 512 MiB = 6448 MiB ≈ 6,76 GB`.
- 25 M nodos D3Q19: `need = 25e6 × 224 B + 0,54 GB = 5,60 + 0,54 = 6,14 GB`. Cabe, y queda por debajo de 7,2 GB (NFR-02).
- Máximo admisible: `(6,76 GB − 0,54 GB) / 224 B ≈ 27,8 M nodos`, coherente con el «≈28 M» de US-10.

### Coarsening

Si `need > budget`:

1. `dx' = dx × (need / budget)^(1/d)`, con d = 2 en 2D y d = 3 en 3D.
2. `dx'` se redondea hacia arriba al múltiplo de 0,25 m y se recalcula la malla con las reglas BR-16 (sin recortar márgenes).
3. Se comprueba la resolución mínima: la dimensión horizontal más pequeña de cualquier edificio debe abarcar al menos 4 celdas. Además, en 3D se recomienda H_min/dx ≥ 10; por debajo, se añade el aviso `low_resolution`.
4. Si con `dx'` ya no se cumplen las 4 celdas, la `api` rechaza con 422 `mesh_too_large`, `rejected_reason="resolution_too_coarse"` y una explicación.

Ejemplo: 40 M nodos a dx = 1,0 m. `need = 9,50 GB` y `budget = 6,76 GB`, así que el factor es `(1,405)^(1/3) = 1,120`. Resulta dx' = 1,12, que se redondea a **1,25 m**, con ≈20,5 M nodos.

### Contrato de respuesta

`POST /simulations/estimate` devuelve `{device, nodes, memory_bytes, budget_bytes, fits, proposed_dx_m, rejected_reason, eta_seconds, grid}`.

`POST /simulations` se comporta así:

- Con `auto_coarsen=true`, aplica `proposed_dx_m` y lo registra en `warnings`.
- Sin `auto_coarsen`, responde 422 `mesh_too_large` con `proposed_dx_m`.

El `solver` vuelve a comprobar la memoria antes de reservar (SOL-19).

## Alternativas rechazadas

- **Recortar los márgenes de dominio de BR-16.** Viola una regla de producto y contamina K con bloqueo y reflexiones.
- **Poblaciones en fp16 o precisión mixta.** Arriesga la estabilidad con τ cerca de 0,5 y rompe la equivalencia de ≤2 % con CPU.
- **Refinamiento multirresolución (mallas anidadas).** Su complejidad no es asumible en R1. Queda como posible evolución.
- **Pasar más allá del 85 % de VRAM.** En WSL2, el escritorio de Windows comparte la VRAM, y los OOM serían intermitentes.

## Consecuencias

Positivas:

- El usuario ve memoria, presupuesto y ETA antes de lanzar.
- Los casos grandes se adaptan solos o se explican.

Negativas y riesgos:

- Las constantes son estimaciones. El benchmark (SOL-18) mide el pico real, y si difiere más de un 10 % se ajustan en el contrato.
- Si el solver no está en línea, la estimación usa el último registro, o el modo CPU con un aviso.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** dominio `simulations/estimate`, con pruebas que reproduzcan los ejemplos numéricos de este ADR.
- **WP-SOLVER:** SOL-19 y publicar `vram_total` y `ram_budget`.
- **WP-WEB:** mostrar la estimación en SCR-12.
