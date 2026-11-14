# ADR-08 — Datos externos de Open-Meteo a través de la api, con caché en Postgres

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos sobre los datos externos:

- **Ubicación y clima:** geocodificación (US-02), altitud (FR-12), rosa ERA5 de ≥10 años (FR-14) y caché reutilizable sin red (FR-15).
- **Privacidad (NFR-15):** solo salen del equipo coordenadas redondeadas y el texto de búsqueda.
- **Restricciones:** C-6 (solo Open-Meteo, sin clave) y BR-18 (sin ubicaciones predefinidas).
- **Supuestos:** A-1 a A-3.

## Decisión

Solo la `api` habla con Open-Meteo, a través de `httpx` con un tiempo de espera de 20 s. Las URL se configuran con `OPEN_METEO_*_URL`.

| Tipo | Endpoint | Clave de caché | TTL |
|---|---|---|---|
| `geocode` | `/v1/search?name=…&count=10&language=es` | texto normalizado (minúsculas, sin espacios extremos) | 30 d |
| `elevation` | `/v1/elevation` | lat/lon redondeadas a 4 decimales (las mismas que se envían) | 365 d |
| `era5` | `archive-api /v1/archive`, `hourly=wind_speed_10m,wind_direction_10m`, `wind_speed_unit=ms`, `models=era5` | lat/lon redondeadas a 0,1° y `period_years` | 365 d |

- La tabla `external_cache` tiene PK `(kind, key)` y guarda `payload jsonb`, `fetched_at` y `expires_at`.
- Una entrada caducada se sigue sirviendo, marcada `stale`, si la red falla.
- **Periodo ERA5:** los últimos `period_years` años naturales completos, terminando el 31 de diciembre del año anterior.
- **Rosa de vientos:**
  - 16 sectores centrados en 0°, 22,5° … 337,5°, con la convención meteorológica «desde».
  - Calma: viento < 0,5 m/s.
  - Por sector se calculan la frecuencia, la media, p50, p90, el máximo y Weibull k y c (máxima verosimilitud con `scipy.stats.weibull_min` y `floc=0`).
- **Errores:** sin red y sin caché, la `api` responde 503 (`era5_unavailable`, `elevation_unavailable` o `geocoding_unavailable`) con una pista para usar la entrada manual (FR-16).
- **Pruebas:** usan respuestas grabadas y coordenadas sintéticas. Nunca hay coordenadas por defecto en el código.

## Alternativas rechazadas

- **Llamadas directas desde el navegador.** Saldrían coordenadas exactas, no habría caché compartida ni uso sin red, y la lógica de la rosa estaría duplicada en el cliente.
- **Datos de estaciones (NOAA ISD, Meteostat).** La cobertura es irregular, a menudo requieren clave y la calidad varía. ERA5 cubre el mundo de forma homogénea (A-2).
- **Caché en disco.** Postgres ya está en el sistema, es transaccional y es fácil de consultar y purgar.

## Consecuencias

Positivas:

- Hay un único punto de salida a internet, que se puede auditar.
- Funciona sin red después de la primera consulta.
- La privacidad queda acotada.

Negativas y riesgos:

- El redondeo a 0,1° comparte la rosa entre proyectos cercanos. Es intencional y equivale a la resolución de ERA5.
- Si Open-Meteo cambia su API, solo hay que actualizar un cliente.
- La consulta de 10 años (~87.600 filas) tarda unos segundos. Se hace de forma síncrona y la UI muestra un indicador de carga.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** dominios `geo` y `wind`, con prueba de cero llamadas salientes cuando hay acierto de caché.
- **WP-WEB:** SCR-05 y SCR-10, con mensajes que explican la causa y la solución.
