# ADR-11 — Criterio de convergencia y promediado temporal (Q-2)

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Q-2 y el supuesto A-10 piden definir el criterio de convergencia y de promediado del LBM 3D. Los flujos alrededor de edificios son no estacionarios: el 2D presenta desprendimiento de vórtices y el 3D es LES. K debe ser un **promedio temporal** estadísticamente estable (BR-01, FR-42).

Además, el resultado debe ser determinista en duración para estimar el ETA:

- **NFR-02:** 3D en ≤60 min.
- **NFR-01:** 2D en ≤2 min con GPU.
- **US-10:** tiempo restante visible.

## Decisión

### Unidad de tiempo

El flujo-a-través es `FT = nx_sim / u_lat` pasos, con `u_lat = 0,05` (ADR-14). Ejemplo: con nx = 550, 1 FT = 11.000 pasos.

### Fases

| Parámetro | plan2d / section2d | volume3d |
|---|---|---|
| Arranque sin promediar (`spinup_flow_throughs`) | 2,0 FT | 1,5 FT |
| Promediado mínimo (`min_avg_flow_throughs`) | 2,0 FT | 2,0 FT |
| Promediado máximo (`max_avg_flow_throughs`) | 8,0 FT | 6,0 FT |
| Intervalo de comprobación | 0,25 FT | 0,25 FT |
| Tolerancia | 1 % | 1 % |
| Comprobaciones consecutivas | 3 | 3 |

### Promedios acumulados

Durante el promediado se acumulan Σu y Σu² por celda.

- 2D: todo el campo.
- 3D: el dominio completo para u y u² en los cortes que se exportan, y la capa z_a para K.

### Prueba de convergencia

En cada comprobación k, sobre la ventana de interés (las celdas fluidas de la malla de salida a la altura z_a):

- `rel_L2 = ‖Ū_k − Ū_{k−1}‖₂ / ‖Ū_k‖₂`, donde Ū es la magnitud del promedio acumulado.
- `rel_mean = |mean(Ū_k) − mean(Ū_{k−1})| / mean(Ū_k)`.

Hay convergencia cuando, una vez superado el promediado mínimo, `rel_L2 < 0,01` y `rel_mean < 0,01` en 3 comprobaciones consecutivas.

### Tope

Si se alcanza el promediado máximo, el trabajo termina `completed` con:

- `convergence.converged = false`.
- El aviso `convergence_cap_reached`, que la UI muestra con lenguaje sencillo («El promedio no se estabilizó del todo; compara con prudencia»).

### Progreso y ETA

- `progress = pasos_hechos / pasos_máximos`, donde `pasos_máximos = (spinup + max_avg) × FT`.
- Si converge antes, salta a 1.
- `eta_seconds = (pasos_máximos − hechos) × nodos / MLUPS_medidos`, recalculado con el MLUPS real de la ejecución.

### Manifiesto

`manifest.convergence = {converged, flow_throughs_spinup, flow_throughs_averaged, rel_change_last, checks}`.

## Alternativas rechazadas

- **Criterio de residuos estacionarios** (p. ej., < 1e-4). No tiene sentido en un flujo LES no estacionario: el residuo instantáneo nunca baja.
- **Número fijo de pasos.** O desperdicia tiempo en casos simples o promedia de menos en casos con estelas largas.
- **Convergencia por sondas puntuales.** Es sensible a dónde se colocan. La norma sobre la capa z_a cubre todo lo que se reporta.

## Consecuencias

Positivas:

- K está promediado de forma reproducible y hay una cota superior de tiempo para el ETA.
- El usuario ve cuándo un resultado no convergió.

Negativas y riesgos:

- Con 6 FT en 3D y nx ≈ 550, el peor caso son 82.500 pasos. A 25 M nodos eso exige ≥570 MLUPS para cumplir 60 min, y ≈400 MLUPS en el caso típico de 3,5 FT. Si no se alcanza, se renegocia según A-8.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** implementa SOL-10 con exactamente estos parámetros, que vienen en `payload.convergence`.
- **WP-API:** escribe los valores por defecto en el `payload`.
- **WP-WEB:** muestra el estado de convergencia en SCR-13 y SCR-14.
