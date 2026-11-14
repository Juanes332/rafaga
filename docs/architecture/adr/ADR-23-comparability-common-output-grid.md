# ADR-23 — Comparabilidad: malla de salida común del proyecto y `comparability_key`

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos relacionados:

- **BR-04:** reducción si ΔK < −0,1, solo con la misma dirección y resolución.
- **BR-11:** dos resultados son comparables solo si comparten dirección, U_ref, z0 y resolución.
- **FR-46** y **US-13:** comparador; si las simulaciones no son compatibles, se bloquea y se explica qué difiere.
- **FR-44:** Lawson combina varias direcciones en las mismas celdas.

Las alternativas añaden fachadas que sobresalen de los edificios. Si cada simulación dimensionara su propio dominio, las mallas no coincidirían.

## Decisión

### Malla de salida

La `api` define la malla de salida del proyecto (`grid.output`): norte arriba, en coordenadas ENU locales.

- Rectángulo envolvente de **los edificios del caso base**.
- Ampliado por `max_facade_extent_m`, la mayor proyección exterior posible de fachadas según los rangos máximos de las estrategias (vuelo de marquesina de 6 m, vegetación con desplazamiento más ancho, aletas y celosías).
- Ampliado además por `2 · H_max` en cada lado.
- Se ajusta a múltiplos de dx. El origen se redondea hacia abajo a un múltiplo de dx, para que la malla sea idéntica con el mismo dx.

Esa malla depende solo de la geometría base, de dx, del tipo y de z_a. Por eso es la misma para todas las alternativas y direcciones.

### Mallas de simulación

Cada dirección tiene su malla de simulación (`grid.sim`), rotada y con márgenes BR-16, que siempre contiene la malla de salida. El `solver` remuestrea de forma bilineal la malla rotada sobre la de salida. En los cortes, la malla de salida es el plano (s, z) de la línea.

### Clave de comparabilidad

`comparability_key = sha256(json_canónico({kind, direction_deg, z0_m, u_ref_ms, dx_m, output_grid, analysis_height_m, section_line|null}))`

- La calcula la `api` al crear el trabajo y el `solver` la copia en `results`.
- `GET /comparisons/check` compara las claves. Si difieren, responde 422 `results_incomparable` con `differences[{field, a, b}]` campo a campo.
- Excepción: cuando el viento de ambas es ERA5, `u_ref_ms` es nominal (K es adimensional) y se fija a la misma constante de referencia (10 m/s), para que las simulaciones de un mismo proyecto sean comparables.

### Cambios en la geometría base

Si cambia la geometría base, cambian la malla y la clave. Los resultados antiguos dejan de ser comparables con los nuevos, y la UI lo explica.

## Alternativas rechazadas

- **Remuestrear al comparar mallas distintas.** El error de interpolación aparecería como ΔK y podría crear falsas zonas de reducción.
- **Dominio por alternativa con recorte a la intersección.** Rompe Lawson multi-dirección y genera bordes inconsistentes.
- **Comparar por identificadores de trabajo en lugar de por clave.** No puede explicar qué difiere.

## Consecuencias

Positivas:

- ΔK celda a celda exacto, Lawson coherente y explicaciones claras de incompatibilidad.

Negativas y riesgos:

- La malla de salida es algo mayor que lo estrictamente necesario.
- Los edificios añadidos fuera del rectángulo base tras crear alternativas cambian la malla, y se avisa.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** cálculo determinista de la malla y de la clave, con una prueba de igualdad entre alternativas.
- **WP-SOLVER:** escribe en `grid.output` exactamente.
- **WP-WEB:** muestra las diferencias de la respuesta 422 en SCR-18.
