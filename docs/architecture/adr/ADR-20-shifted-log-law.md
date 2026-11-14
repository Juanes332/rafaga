# ADR-20 — Ley logarítmica desplazada para el perfil de viento

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos y reglas implicados:

- **BR-07:** perfil `U(z) = (u*/κ)·ln(z/z0)`, con κ = 0,41.
- **BR-08:** categorías de rugosidad de hasta z0 = 2,0 m (urbano denso).
- **BR-15:** altura de análisis entre 0,5 y 3,0 m, con 1,5 m por defecto.
- **BR-01:** K = U(z_a)/U_ref(z_a).
- **FR-18:** perfil de entrada.

Con z0 = 2,0 m y z_a = 1,5 m, la forma literal da ln(0,75) < 0, es decir, una velocidad negativa. Con z0 = 1,0 m y z_a = 1,0 m da 0. K quedaría indefinido justo en los casos urbanos densos, que son los más relevantes.

## Decisión

Se usa la forma desplazada en todo el sistema (`api`, `solver` e informes):

`U(z) = (u*/κ) · ln((z + z0) / z0)`, con κ = 0,41.

`u* = κ · U10 / ln((10 + z0) / z0)`

Propiedades:

- `U(0) = 0` y U es monótona creciente para todo z ≥ 0.
- Para z ≫ z0 coincide con BR-07: el error relativo es < 3 % si z > 30·z0.
- `U_ref(z_a)` siempre es positiva, así que K está siempre definido.

Dónde se aplica:

- Perfil de entrada en el corte y en 3D (ADR-12).
- Referencia de K.
- Traslado de ERA5 al sitio en Lawson (ADR-15).
- Valor `ustar_ms` que muestra `GET /projects/{id}/wind`.

La SPA y el informe muestran la fórmula usada, con una nota: «Forma desplazada para que el perfil esté definido cerca del suelo en terrenos muy rugosos».

## Alternativas rechazadas

- **Altura de desplazamiento d:** `U = (u*/κ)·ln((z − d)/z0)`. Introduce un parámetro que el usuario no puede estimar, y queda indefinido para z < d + z0, que es justo la zona peatonal.
- **Acotar z a max(z, k·z0).** K sería discontinuo y dependería de una constante arbitraria.
- **Prohibir z0 > z_a.** Eliminaría la categoría urbano denso de BR-08.

## Consecuencias

Positivas:

- K está definido en todo el rango de parámetros y las implementaciones son coherentes.

Negativas y riesgos:

- Es una desviación documentada de la redacción literal de BR-07. Se informa al product owner en `architecture.md`.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** función de perfil en el dominio `wind`, con pruebas de coincidencia asintótica.
- **WP-SOLVER:** la misma fórmula en `boundary` y `comfort`.
- **WP-WEB:** muestra la fórmula en SCR-10.
