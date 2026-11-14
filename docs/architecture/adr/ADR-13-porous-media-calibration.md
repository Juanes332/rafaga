# ADR-13 — Calibración de medios porosos: celosías, vegetación y elementos sub-celda (Q-3)

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Q-3 pregunta por la calibración de la porosidad: Darcy-Forchheimer o bounce-back parcial. Requisitos relacionados:

- **FR-29:** celosía porosa parametrizada por porosidad.
- **FR-33:** vegetación con LAD, modelada como medio poroso.
- **US-10:** porosidad también en 3D.
- **BR-10:** porosidad entre 5 % y 95 %, con 40 % por defecto.

Además, las aletas de 0,15 m de espesor con paso de 1 m no se pueden resolver con dx = 1 m. Hace falta una regla general para los sólidos más finos que una celda.

## Decisión

Toda la resistencia porosa se aplica como fuerza de volumen de Forchheimer, mediante el esquema de forzamiento de Guo.

### Actualización semi-implícita de la velocidad

Es necesaria para que sea estable con ζ grande:

`u = (Σ f c + F_explícito/2) / (ρ · (1 + ½ · a · |u*|))`

- `a` es el coeficiente cuadrático por celda.
- `u*` es la velocidad sin forzamiento.

### Celosía (screen)

Coeficiente de pérdida de Idelchik para una placa perforada delgada de bordes vivos. β es la porosidad (fracción abierta):

`ζ(β) = ((0.707·√(1−β) + 1 − β) / β)²`

| β | ζ |
|---|---|
| 0,05 | 1074,66 |
| 0,20 | 51,29 |
| 0,40 (por defecto) | 8,23 |
| 0,60 | 1,99 |
| 0,95 | 0,048 |

- Grosor de capa: `Δn = max(dx, thickness_m)`, es decir, al menos una celda.
- Fuerza: `F = −ρ · ζ/(2Δn) · |u_n| · u_n · n̂`, solo sobre la componente normal `u_n = u·n̂` (en unidades de retícula, con Δn en celdas).
- La `api` calcula `loss_coefficient` y la `normal` en la escena, y el `solver` las usa tal cual.

### Vegetación

`F = −ρ · C_d · LAD · |u| · u`, isotrópica.

- `C_d = vegetation_cd = 0,2` es un ajuste del usuario.
- LAD (m²/m³) se convierte a unidades de retícula como `LAD · dx`.
- No se añaden términos de fuente de turbulencia en R1.

### Sólidos sub-celda

Es una regla general del voxelizador:

- La cobertura de cada celda se calcula por supermuestreo 4× por eje (16 muestras en 2D, 64 en 3D).
- Cobertura ≥ 0,5: celda sólida (pared).
- 0 < cobertura < 0,5 en una primitiva sólida: celda porosa tipo celosía, con `β = 1 − cobertura`, ζ(β) de Idelchik y la normal de la primitiva. La normal de una aleta es perpendicular a su cara mayor.

Así, las aletas, marquesinas finas o barandillas más delgadas que dx mantienen su efecto de bloqueo en lugar de desaparecer o convertirse en muros.

## Alternativas rechazadas

- **Bounce-back parcial (Walsh et al.).** La relación entre el parámetro y la pérdida de carga depende de τ, y por tanto de la resolución. Su calibración es menos transparente para un arquitecto.
- **Término lineal de Darcy.** Con Re ~1e6, el régimen inercial domina y el término viscoso no aporta.
- **Ignorar los elementos sub-celda.** Las estrategias de aletas y celosías finas no tendrían ningún efecto con dx habituales y la comparación sería engañosa.
- **Forzar dx < espesor del elemento.** Haría explotar la memoria (ADR-10).

## Consecuencias

Positivas:

- La calibración es física y trazable: la porosidad del usuario se traduce en ζ.
- La celosía tiene un efecto monótono con β.
- Los elementos finos siguen representados.

Negativas y riesgos:

- La fórmula de Idelchik es para placas perforadas. Para lamas orientadas es una aproximación, documentada como limitación (C-9).
- Con ζ > 500 la semi-implicitud es imprescindible. Hay que probar la estabilidad con β = 0,05.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** calcula ζ en la escena.
- **WP-SOLVER:** módulos `services/porous` y `services/voxelize`, con pruebas de pérdida de carga en canal 2D. El Δp medido debe estar dentro del ±15 % de ζ·½ρu² para β = 0,2, 0,4 y 0,6.
