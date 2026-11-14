# ADR-15 — Confort Lawson LDDC: tabla por defecto y cálculo de excedencia (Q-5)

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Q-5 pide verificar las tablas Lawson LDDC (supuesto A-9). Requisitos relacionados:

- **BR-05:** confort LDDC ponderado por la rosa, con umbrales editables.
- **BR-12:** como máximo 16 sectores; el resultado es parcial con menos del 95 % de cobertura.
- **FR-44** y **US-12**.

Las simulaciones dan K por dirección, y la rosa ERA5 (ADR-08) da la distribución de U10 por sector a escala de malla regional (A-3).

## Decisión

### Tabla por defecto

Es editable en Ajustes (`user_settings.lawson`).

Confort, con excedencia del 5 % del tiempo:

| Clase | Clave | Umbral |
|---|---|---|
| A | `sitting` (sentarse largo tiempo) | 4 m/s |
| B | `standing` (estar de pie, entradas) | 6 m/s |
| C | `strolling` (pasear) | 8 m/s |
| D | `business_walking` (caminar con propósito) | 10 m/s |
| E | `uncomfortable` (incómodo) | > 10 m/s |

Seguridad, con excedencia del 0,025 % del tiempo (≈2,2 h/año):

- `unsafe_frail`: 15 m/s (personas vulnerables, ciclistas).
- `unsafe_all`: 20 m/s (público general).

Todos los valores proceden del criterio LDDC publicado por Lawson. Se pueden editar, y la UI recuerda que son valores por defecto que debe confirmar el profesional.

### Traslado de ERA5 al sitio

Se usa una altura de mezcla `h_b = 60 m` y rugosidad de referencia ERA5 `z0_ref = 0,03 m`. La rugosidad del sitio es `z0_s`, y z_a es la altura de análisis.

`T = [ln(h_b/z0_ref) / ln((10+z0_ref)/z0_ref)] · [ln((z_a+z0_s)/z0_s) / ln(h_b/z0_s)]`

Así, `U_ref(z_a) = T · U10_ERA5`. Ejemplo: con z0_s = 1,0 m y z_a = 1,5 m, T = 1,308 × 0,224 = 0,293.

### Velocidad efectiva

Factor GEM: `G = max(1, (1 + 3·I) / 1,85)`. I es la intensidad de turbulencia local:

- En 3D, se toma de la LES (σ_u/Ū a z_a).
- En 2D, se toma `turbulence_intensity_default = 0,25` de los ajustes.

Así, `U_eff = G · K_d · T · U10`, que equivale a max(media, GEM).

### Excedencia por celda para un umbral U_t

Cada sector simulado d ∈ S tiene frecuencia f_d y una distribución Weibull (k_d, c_d) de U10:

`P(U_eff > U_t) = (1/C) · Σ_{d∈S} f_d · exp(−(U_t / (G·K_d·T·c_d))^{k_d})`

- La cobertura es `C = Σ_{d∈S} f_d / (1 − f_calm)`.
- Las calmas no exceden ningún umbral.

### Clasificación

- La clase de confort es la menor cuyo umbral cumple P ≤ 5 %. Si ninguna lo cumple, la clase es E.
- Los indicadores de seguridad se activan cuando P(15) o P(20) superan el 0,025 %.
- Si `C < 0,95`, el resultado se marca `partial = true` y la UI muestra la cobertura (BR-12).
- Con viento en modo manual no hay distribución, y la `api` responde 409 `rose_missing`.

### Salidas

Las produce el trabajo `aggregate` del `solver` (SOL-12):

- `lawson_class.u8` (0–4) y `safety.u8` (bits).
- `exceedance.f32` con forma [n_thresholds, ny, nx].
- `lawson.png`.
- La fila `comfort_results` con las áreas por clase.

El `lawson_hash` (sha256 de la tabla) permite recalcular cuando cambia la tabla.

## Alternativas rechazadas

- **Davenport o NEN 8100 como criterio por defecto.** El usuario pidió LDDC. Podrían añadirse como tablas alternativas más adelante.
- **Histograma empírico por sector en lugar de Weibull.** Las colas del 0,025 % son muy ruidosas con 10 años de datos horarios, y la forma cerrada es rápida por celda.
- **No renormalizar por cobertura.** Subestimaría sistemáticamente la excedencia con pocas direcciones. Se prefiere renormalizar y marcar el resultado como parcial de forma visible.
- **Usar U10 de ERA5 sin corrección por rugosidad.** Sobrestimaría la velocidad en entornos urbanos.

## Consecuencias

Positivas:

- Las clases son interpretables, con supuestos explícitos y editables.
- El recálculo tras editar la tabla tarda segundos y no requiere volver a simular.

Negativas y riesgos:

- La aproximación GEM con I fija en 2D es gruesa. Se documenta en el informe junto con el aviso de FR-48.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** SOL-12, con pruebas analíticas (K constante y Weibull conocida, con excedencia en forma cerrada).
- **WP-API:** API-60, API-61 y JOB-A03.
- **WP-WEB:** SCR-15 con notas interpretativas en Literata.
