# ADR-12 — Condiciones de contorno y entrada de capa límite atmosférica (Q-3)

Estado: Aceptada
Fecha: 2026-11-13

> Enmienda (2026-11-13, ADR-27): en `volume3d` la perturbación sembrada del 2 % se sustituye por turbulencia de entrada sintética (Xie y Castro) con I_u(z) objetivo de 0,15 a 0,30. La desviación "Equilibrium ABL" del solver (longitud de mezcla estacionaria κ·(z + z0) en 3D, apartada de C-3) queda **sustituida**; se conservan la ley de pared en la primera capa y la fuerza de cortadura en el techo.

## Contexto

Q-3 pregunta por el tratamiento de la entrada de capa límite atmosférica (ABL) en LBM. Requisitos relacionados:

- **FR-18:** perfil logarítmico de entrada con z0.
- **BR-07** y **BR-08:** z0 de hasta 2,0 m.
- **BR-16:** márgenes de dominio.
- **OOS-5:** terreno plano.

Con dx ≈ 1-2 m no se puede resolver la rugosidad: z0 es comparable a dx, o mayor. El perfil debe mantenerse horizontalmente homogéneo hasta los edificios, y las reflexiones en la salida no deben contaminar las estelas.

## Decisión

Los ejes de la malla de simulación están rotados para que el viento entre por −x y salga por +x (ADR-04).

| Contorno | plan2d (x-y) | section2d (s-z) y volume3d |
|---|---|---|
| Entrada (x = 0) | Velocidad uniforme `U_ref(z_a)`, que en unidades de retícula es `u_lat` | Velocidad con perfil logarítmico desplazado (ADR-20) |
| Salida (x = nx−1) | Presión, ρ = 1 | Presión, ρ = 1 |
| Laterales | Deslizamiento libre (reflexión especular) | Deslizamiento libre (3D) |
| Techo | — | Deslizamiento libre |
| Suelo | — | Bounce-back a medio camino con ley de pared logarítmica |
| Edificios y sólidos | Bounce-back a medio camino | Bounce-back a medio camino |

### Entrada (velocidad)

Se usa una condición de contorno regularizada (Latt et al.):

- Las poblaciones desconocidas se reconstruyen como f^eq(ρ, u) + f^neq regularizado a partir de Π^neq.
- ρ se extrapola de la primera celda interior.

Perfil 3D y de corte: `u(z) = (u*/κ)·ln((z + z0)/z0)`, con κ = 0,41. Se escala para que en la cota superior del dominio u = u_lat = 0,05, así que el número de Mach máximo de entrada es 0,087.

En 3D se añade una perturbación aleatoria con semilla del 2 % de u(z) en las tres componentes, aplicada solo en la capa de entrada para disparar la transición. La semilla viene en `payload.physics.seed`.

### Salida

Condición de presión regularizada con ρ = 1 (extrapolación de no-equilibrio).

Además hay una capa esponja en el último 10 % de nx: τ crece linealmente desde τ_eff hasta 1,0 dentro de la esponja, para absorber las ondas acústicas y los vórtices salientes. La ventana de salida (ADR-23) nunca invade la esponja.

### Laterales y techo

Reflexión especular: la población que sale vuelve con la componente normal invertida, y no hay esfuerzo cortante.

### Suelo con ley de pared

Es un muro con bounce-back a medio camino, más una fuerza de arrastre (forzamiento de Guo) en la primera capa fluida z₁ = dx/2:

- `τ_w = ρ · (κ · |U₁| / ln((z₁ + z0)/z0))²`
- `F = −(τ_w / dx) · U₁/|U₁|`, aplicada a la componente horizontal.

Esto reproduce la tensión superficial de la ley logarítmica sin resolver la rugosidad, y mantiene el perfil a lo largo del fetch de 5H.

### Sólidos

Bounce-back a medio camino sobre la máscara voxelizada. Los sólidos sub-celda pasan a ser porosos (ADR-13).

### Plano 2D en planta

No hay suelo. K se refiere a la velocidad de entrada, que representa U_ref(z_a) del campo libre.

## Alternativas rechazadas

- **Entrada Zou-He.** Es inestable cuando τ está cerca de 0,5 y con alto Reynolds efectivo. La regularizada es más robusta.
- **Dominio periódico en la dirección del flujo con precursor.** Duplica el coste y obliga a gestionar una simulación precursora.
- **Techo sin deslizamiento.** Genera una capa de cortadura espuria y acelera el núcleo.
- **Resolver los elementos de rugosidad.** Inasumible con dx de 1 m.
- **Sin capa esponja.** Las reflexiones de presión en la salida contaminan el promedio en dominios de 15H.

## Consecuencias

Positivas:

- Perfil estable, salida limpia y comportamiento coherente entre corte y 3D.

Negativas y riesgos:

- La ley de pared es una aproximación de equilibrio, que es aceptable en una herramienta de anteproyecto (C-9).
- La perturbación del 2 % no reproduce la turbulencia atmosférica real. Por eso la intensidad de turbulencia de entrada para el GEM se toma del ajuste por defecto en 2D (ADR-15).

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** módulo `services/boundary`, con pruebas unitarias por contorno y SOL-16 (AIJ) como validación integral.
- **WP-API:** pasa z0, z_a y `seed` en el `payload`.
