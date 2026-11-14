# ADR-14 — Conversión de unidades LBM y estabilidad

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

La simulación debe ser estable y cumplir a la vez:

- **FR-37:** LES Smagorinsky.
- **NFR-16:** validación científica.
- **FR-41:** Strouhal y AIJ caso A.

El flujo urbano real tiene Re_H ~ 10⁶–10⁷. Con la viscosidad física del aire, el τ molecular resultante queda prácticamente en 0,5, y el esquema sería inestable. El usuario pidió un número de Mach de retícula ≤ 0,1.

## Decisión

### Escalas

- `u_lat = 0,05` es la velocidad de referencia de entrada: la cota superior del perfil en 3D y en corte, y el valor uniforme en planta. Como `c_s = 1/√3`, el Mach de entrada es `0,05·√3 = 0,087 ≤ 0,1`.
- `dt = u_lat · dx / U_phys`, donde U_phys es la velocidad física en la misma cota.
- `ν_lat = max(ν_phys · dt / dx², ν_floor)`, con `ν_phys = 1,5e-5 m²/s` y `ν_floor = 5e-5`.
- `τ0 = 0,5 + 3 · ν_lat`.

### Turbulencia de submalla

Smagorinsky local, según Hou et al. (1996). Se calcula a partir del tensor de no-equilibrio `Π^neq = Σ c c (f − f^eq)`:

`τ_eff = ½ · (τ0 + √(τ0² + 18·√2 · C_s² · |Π^neq| / ρ))`, con `C_s = 0,17`.

`τ_eff` se acota a `[0,5005, 2,0]`.

### Colisión

BGK regularizado: antes de colisionar, f^neq se proyecta sobre Π^neq. Esto filtra los modos fantasma y da estabilidad con τ cerca de 0,5.

### Guardas

Cada 100 pasos se calcula el Mach local máximo. Si `max|u|/c_s > 0,35` o aparece algún NaN, el trabajo falla con `error_code=numerical_instability`.

La pista que se da al usuario es: «Aumenta el tamaño de celda o revisa elementos con porosidad muy baja».

### Ejemplo (dx = 1 m, U_phys = 10 m/s en la cota de referencia)

- `dt = 0,05 · 1 / 10 = 0,005 s`.
- `ν_phys · dt / dx² = 1,5e-5 · 0,005 = 7,5e-8`, por debajo del suelo. Se usa `ν_lat = 5e-5`.
- `τ0 = 0,5 + 3·5e-5 = 0,50015`. La LES aporta la mayor parte de τ_eff en zonas de cortadura.
- Re de celda efectivo: `u_lat · 1 / ν_lat = 1000`.
- Con un edificio de H = 26 celdas: `Re_H = 0,05 · 26 / 5e-5 = 26.000`.
- 1 FT con nx = 550 son 11.000 pasos, es decir, 55 s de tiempo físico.

### Justificación de la independencia de Reynolds

Los flujos alrededor de cuerpos romos con aristas vivas tienen la separación fijada por la geometría. Por encima de Re_H ≈ 2·10⁴ (criterio de Snyder para túneles), los patrones medios son prácticamente independientes de Re. Por eso se acepta un Re efectivo de retícula ≥ 2·10⁴ en lugar del físico.

El `solver` añade el aviso `low_reynolds` cuando `Re_H` efectivo < 2·10⁴, lo que ocurre con edificios de menos de ~20 celdas de altura.

### Excepción: validación

Para la validación (SOL-15, cilindro cuadrado con Re = 150) se fija ν_lat a partir de Re, sin suelo y sin LES (C_s = 0).

## Alternativas rechazadas

- **Igualar el Re físico.** τ → 0,5 provoca una inestabilidad inmediata.
- **u_lat = 0,1.** El Mach de entrada sería 0,17 y en las esquinas ~0,35, con errores de compresibilidad de orden Ma² ≈ 3–12 %.
- **Colisión MRT o cumulantes.** Mayor coste y complejidad. Regularizado más LES basta para esta aplicación, y los cumulantes podrían estudiarse en una versión posterior si la validación lo exige.
- **Smagorinsky dinámico.** Requiere un filtrado de prueba costoso. C_s fija es estándar en LBM urbano.

## Consecuencias

Positivas:

- Es estable en todo el rango de uso, con parámetros explícitos en el `payload` (`physics.u_lattice_ref`, `smagorinsky_cs`, `nu_lattice_floor`, `tau_bounds`).
- K es adimensional, así que U_phys solo fija el tiempo físico y la interpretación.

Negativas y riesgos:

- Los resultados dependen de la resolución cuando H tiene menos de 10 celdas, y se avisa al usuario.
- La comparación absoluta con mediciones es cualitativa (C-9).

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** implementa la conversión y las guardas, con pruebas unitarias de τ_eff y de los límites.
- **WP-API:** fija los valores de `physics` en el `payload`.
