# ADR-24 — Importadores de geometría: DXF, STL, OBJ e IFC hacia edificios con escalones

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos relacionados:

- **US-03:** importar DXF, STL y OBJ (Must) e IFC (Should).
- **FR-20, FR-21, FR-22** y **D-5:** librerías de lectura a decisión del arquitecto.
- **FR-26:** validación.
- **NFR-22:** DXF R2000+, STL binario y ASCII, OBJ, IFC2x3 e IFC4.
- **NFR-14:** ≤100 MB.

Las fachadas se aplican a **aristas de huellas** (US-08), así que la geometría debe acabar como huellas extruidas.

## Decisión

Todo importador produce `Building {footprint, holes, height_m, tiers?, source, missing_height}` en metros locales.

### DXF (`ezdxf`)

- Se aceptan `LWPOLYLINE` y `POLYLINE` cerradas (`closed` o con el primer vértice igual al último, con tolerancia de 1 mm).
- La altura se toma en este orden:
  1. XDATA o atributo `height`.
  2. Número en el nombre de la capa (`EDIF_24`, `h=12.5`).
  3. Si no hay ninguno, `missing_height=true` y altura provisional 0. FR-26 bloquea la simulación hasta que el usuario asigne una.
- Las polilíneas abiertas y las entidades de otros tipos se informan en `ignored[{entity, reason}]`.
- La unidad se toma de `$INSUNITS` y se convierte a metros. Si no está definida, se asume metros y la UI pide confirmarlo.

### STL y OBJ (`trimesh`)

- Se separa el modelo por cuerpos conexos.
- Cada cuerpo se corta horizontalmente cada 3 m, desde su z mínima, y se calcula la huella de cada corte con `shapely` (unión de polígonos y simplificación a 5 cm).
- Los cortes consecutivos con la misma huella se fusionan en un mismo escalón (`tiers`).
- La huella base es la del primer corte y `height_m` es la z máxima menos la mínima.
- Se detecta la unidad por la extensión típica (> 2000 sugiere mm, < 2 sugiere km). La UI la confirma.

### IFC (`ifcopenshell`, R2)

- Se recorren `IfcBuilding`, `IfcBuildingStorey` y los `IfcBuildingElement` con geometría.
- Se calcula la caja envolvente alineada a ejes de cada edificio. La huella es el rectángulo y la altura es la extensión en z.
- Los elementos sin geometría o sin representación se informan como ignorados.

### Opciones comunes

- `mode` puede ser `append` o `replace`.
- `center=true` traslada el centro del rectángulo envolvente al origen.
- El archivo original se guarda en `uploads` para trazabilidad.

### Seguridad y errores

- El tipo se comprueba por extensión y por los bytes mágicos.
- El parseo tiene un tiempo límite de 60 s.
- Si el archivo es corrupto, la respuesta es 422 `import_failed` con la causa y una sugerencia (por ejemplo, «Exporta el DXF como R2000 con polilíneas cerradas»), y el proyecto no cambia.

## Alternativas rechazadas

- **Pasar las mallas crudas al `solver` y voxelizarlas.** No se podrían añadir fachadas por arista, el `solver` tendría que tratar mallas no estancas y las escenas dejarían de ser uniformes (ADR-04).
- **Una sola huella por cuerpo, sin escalones.** Se perderían los retranqueos y voladizos existentes.
- **Extrusión real de la geometría IFC.** Es costosa y frágil con modelos BIM heterogéneos. R2 acepta la caja envolvente, como dice FR-22.
- **Usar FreeCAD u Open CASCADE.** Dependencias pesadas para lo que se necesita.

## Consecuencias

Positivas:

- Una sola representación para el editor, las fachadas y el `solver`.
- Informes de importación accionables.

Negativas y riesgos:

- Las formas curvas o inclinadas se aproximan por escalones de 3 m.
- Las cajas envolventes de IFC sobreestiman el volumen de edificios en L. Se documenta en la UI.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** dominio `imports`, con fixtures pequeños por formato (sin coordenadas geográficas reales) y una cobertura ≥80 %.
- **WP-WEB:** SCR-07, con confirmación de unidad y asignación de alturas faltantes.
