# ADR-19 — El solver produce todos los artefactos numéricos; la api calcula áreas de zona

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos sobre artefactos y zonas:

- **Imágenes e informes:** PNG ≥300 dpi con leyenda, escala, norte y viento de referencia (FR-50); informe PDF (FR-51, NFR-17: ≤30 s con 6 mapas); paletas cmocean (FR-49).
- **Confort:** Lawson (FR-44).
- **Zonas:** recálculo sin re-simular (FR-43), en ≤2 s (NFR-05).

El código de colormaps y de gráficos debe tener un único dueño. El recálculo de zonas no puede esperar detrás de un 3D de 60 min.

## Decisión

### `solver`, carril ligero (ADR-22)

| Tipo de trabajo | Produce |
|---|---|
| `aggregate` | Clases Lawson, excedencias, `lawson.png` y la fila `comfort_results` |
| `render` | PNG de exportación de las capas `k`, `zones`, `speed`, `delta_k` y `lawson` |
| `report` | PDF A4 con WeasyPrint |

- `render` se hace a `dpi` ≥ 300, con la metainformación pHYs, la leyenda numérica con unidades, la barra de escala, la flecha de norte, el viento de referencia (dirección y U10) y la línea de aviso.
- `report` se genera desde una plantilla HTML, con Literata y Hanken Grotesk embebidas y el aviso de FR-48 en el pie de cada página.
- Además, al terminar cada simulación el carril pesado genera las vistas previas a 150 dpi (`k.png`, `speed.png`, `zones.png`) con matplotlib y cmocean.

### `api`

Calcula las áreas de zona con numpy sobre `K.f32`:

- Área de celda = dx².
- Porcentaje sobre el área fluida dentro de la ventana de salida.
- Lo usan `GET /results/{id}/zones` y `GET /comparisons/areas`, con los umbrales como parámetros.

Son operaciones de conteo de milisegundos. No hay colormaps ni gráficos en la `api`.

### Navegador

Re-umbraliza las zonas en el cliente sobre el `Float32Array` de K, de forma inmediata al cambiar un umbral, y dibuja K y ΔK con las LUT cmocean (WEB-04). Esas LUT se generan de las mismas tablas RGB que usa el `solver`.

### Instantánea del informe

La `api` prepara un `payload` completo (proyecto, ubicación, rosa, parámetros, tablas de áreas y lista de mapas). Así el `solver` no consulta tablas de negocio.

## Alternativas rechazadas

- **La `api` renderiza PNG y PDF.** Habría matplotlib y cmocean duplicados en dos imágenes, con riesgo de que las paletas diverjan, y CPU pesada en el proceso que atiende peticiones.
- **PDF generado en el navegador.** No garantiza 300 dpi, la tipografía es inconsistente y no se puede probar en CI.
- **Zonas recalculadas en el `solver` como trabajo.** Esperarían detrás de la cola e incumplirían NFR-05.

## Consecuencias

Positivas:

- Un solo dueño de la apariencia de los mapas.
- Zonas instantáneas.
- Informes reproducibles.

Negativas y riesgos:

- La imagen del solver incluye WeasyPrint (pango y cairo), unos 100 MB.
- Las exportaciones esperan en el carril ligero, que es independiente del pesado.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** SOL-11 a SOL-14.
- **WP-API:** API-57 y API-63 con numpy, y los `payload` de `render`/`report` según el contrato.
- **WP-WEB:** WEB-04 con una prueba de concordancia de LUT (±1/255).
