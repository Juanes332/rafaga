# ADR-09 — Teselas de mapa: OSM raster a través de un proxy autenticado con caché en disco

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Q-4 pregunta por el proveedor de teselas y la política de caché sin red. Otros requisitos relacionados:

- **D-2:** hay que respetar la política de uso de teselas de OSM.
- **NFR-15:** solo salen datos a Open-Meteo y a OSM.
- **US-02:** el usuario ubica el proyecto con un clic en el mapa.
- **C-6:** el sistema debe funcionar con caché o con entrada manual cuando no hay red.

## Decisión

- **Mapa.** MapLibre GL JS con una fuente raster de 256 px. La URL de las teselas es `{apiBase}/tiles/{z}/{x}/{y}.png`, y `transformRequest` añade la cabecera `Authorization`.
- **Proxy en la `api`.** El endpoint `GET /api/v1/tiles/{z}/{x}/{y}.png` funciona así:
  - Valida que z esté entre 0 y 19 y que x e y estén entre 0 y 2^z−1. Si no, responde 422.
  - Busca la tesela en `/data/cache/tiles/{z}/{x}/{y}.png`.
  - Si no la tiene, la descarga de `TILE_URL_TEMPLATE` (por defecto `https://tile.openstreetmap.org/{z}/{x}/{y}.png`) con el `User-Agent` de `TILE_USER_AGENT`.
- **Caché.**
  - Respeta `Cache-Control` y `Expires` del origen, con un TTL mínimo de 7 días.
  - Cuando no hay red, sirve las teselas aunque estén vencidas.
  - Desaloja por LRU (según el `atime` registrado en un índice ligero) por encima de `TILE_CACHE_MAX_MB=500`.
- **Sin red y sin tesela en caché.** La `api` responde 503 `tile_unavailable` y la SPA pinta una rejilla neutra. Las coordenadas se pueden seguir escribiendo a mano.
- **Atribución.** «© OpenStreetMap contributors», visible siempre en el mapa y en las exportaciones que usen el fondo.
- **Descargas.** Nunca hay precarga masiva: solo se descargan las teselas que el usuario ve.
- **Límite de peticiones.** Tiene un presupuesto propio (ADR-26).

## Alternativas rechazadas

- **Navegador directo a OSM.** No se controlan el `User-Agent` ni la caché, no funciona sin red y se pierde el punto único de salida.
- **Teselas vectoriales autoalojadas (extractos regionales o planeta).** Implican descargas de GB que rompen la instalación en ≤15 min (NFR-09), y la app no tiene una región fija.
- **Proveedores con clave (MapTiler, Mapbox).** Exigen una cuenta, y C-6 y C-11 los excluyen.
- **Precarga masiva para uso sin red.** Viola la política de uso de teselas de OSM.

## Consecuencias

Positivas:

- Se pueden volver a ver sin red las zonas ya visitadas.
- Se cumple la política de OSM.
- El proveedor se puede cambiar por configuración.

Negativas y riesgos:

- Un paneo puede pedir decenas de teselas, por eso tienen su propio límite.
- La caché ocupa hasta 500 MB del volumen `rafaga-data`.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** implementa el dominio `tiles` con LRU y sus pruebas, usando un transporte falso.
- **WP-WEB:** implementa `transformRequest`, la atribución y la rejilla de reserva.
- **WP-OPS:** documenta `TILE_URL_TEMPLATE` en el README.
