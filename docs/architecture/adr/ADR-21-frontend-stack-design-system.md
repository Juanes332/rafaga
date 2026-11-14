# ADR-21 — Stack de frontend y sistema de diseño

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos de la interfaz:

- **Flujo y pantallas:** rail de pasos, lienzo e inspector, modo claro y oscuro (FR-52); 3D navegable (FR-27).
- **Visualización:** partículas animadas y `prefers-reduced-motion` (FR-45, US-11); cmocean (FR-49).
- **Accesibilidad:** WCAG 2.2 AA (NFR-07).
- **Rendimiento:** ≤100 ms p95 con 200 bloques (NFR-04).
- **Privacidad:** solo hay tráfico saliente a Open-Meteo y OSM (NFR-15).
- **Idioma:** es-CO externalizado (FR-54).

No se pidió ni MUI ni un estilo de panel de administración, así que aplica `react-senior` + `frontend-design`.

## Decisión

### Estructura

`react-senior`: Vite, TypeScript estricto, TanStack Query/Router/Table, Zustand, shadcn/ui en `components/ui`, CSS Modules y arquitectura de pantalla inversa.

### Componentes de dominio

- **Mapa:** MapLibre GL JS, raster vía el proxy de la `api` (ADR-09).
- **Editor 2D:** SVG en coordenadas métricas, con transformaciones de vista en un store Zustand. El historial de deshacer y rehacer es una pila de comandos con ≥50 niveles. Se elige SVG por la accesibilidad (foco por bloque) y porque 200 polígonos son baratos.
- **3D:** `three` + `@react-three/fiber` + `@react-three/drei` (OrbitControls) para la geometría y el visor de resultados.
- **Campo de partículas (el elemento memorable, WEB-03):**
  - WebGL2 propio, con advección por ping-pong de texturas: posiciones en una textura RGBA32F y velocidad (ux, uy) en una textura RG32F.
  - Estelas con desvanecimiento sobre la textura previa.
  - ≥16k partículas a 60 fps.
  - Con `prefers-reduced-motion` o sin WebGL2, se muestran líneas de corriente estáticas calculadas en el cliente.
- **Colormaps:** LUT de 256 entradas de cmocean `speed` (K) y `balance` (ΔK), generadas desde las tablas RGB publicadas.
- **Gráficos:** rosa de vientos en SVG con `d3-scale` y `d3-shape`.

### Tipografía

Hanken Grotesk para la interfaz y Literata para la lectura (notas interpretativas y ayudas largas). Ambas se autoalojan con `@fontsource`. Las cifras son tabulares.

### i18n

i18next con `src/locales/es-CO/*.json`. Los números se formatean con `Intl.NumberFormat('es-CO')`.

### Tokens

Paleta, escala tipográfica, radios, foco y patrones de zona están definidos en `contracts/design-system.md`.

## Alternativas rechazadas

- **Google Fonts por CDN.** Sale tráfico a un tercero no autorizado por NFR-15.
- **deck.gl.** Es pesado para una sola capa de partículas, y su modelo de datos no aporta nada aquí.
- **Leaflet.** Sin un contexto WebGL compartido para superponer partículas fluidas, y con peor rendimiento al hacer zoom.
- **Canvas 2D para el editor.** La accesibilidad por teclado es peor (no hay foco por elemento) y la selección de aristas tendría que hacerse a mano.
- **MUI o Uko.** No se pidieron. `react-senior` es el stack por defecto.

## Consecuencias

Positivas:

- La interfaz tiene identidad propia.
- No hay tráfico de terceros.
- Las partículas funcionan en GPU integradas.

Negativas y riesgos:

- El motor WebGL propio exige pruebas visuales manuales y un respaldo bien probado.
- El bundle con three y maplibre es grande. Se mitiga con división de código por ruta (el visor 3D y el mapa se cargan de forma diferida) para cumplir NFR-04 (≤3 s de carga).

Qué debe hacer cada paquete de trabajo:

- **WP-WEB:** SCR-01 a SCR-23 y WEB-01 a WEB-05, siguiendo `design-system.md`, con axe-core en CI.
