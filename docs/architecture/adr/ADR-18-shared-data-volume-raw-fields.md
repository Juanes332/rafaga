# ADR-18 — Volumen de datos compartido y campos en float32 crudo

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos de almacenamiento:

- **NFR-12** y **C-5:** solo volúmenes con nombre, sin bind mounts.
- **FR-05:** persistencia.
- **NFR-22:** campos exportables en CSV y NPZ.
- **NFR-05:** recálculo de zonas en ≤2 s.
- **US-11:** campo animado en el navegador.

`api` y `solver` deben compartir subidas, resultados, exportaciones e informes.

## Decisión

### Volúmenes

- `rafaga-db`: datos de Postgres.
- `rafaga-data`: montado en `/data` en `api` y `solver`.

### Propiedad

Ambas imágenes crean `/data` con propietario `10001:10001` y ejecutan como `USER 10001:10001`.

Docker copia la propiedad del punto de montaje de la imagen al volumen vacío la primera vez que lo monta, así que los dos servicios pueden leer y escribir sin root.

### Estructura

El detalle está en `contracts/job-contract.md` §5.

```
/data/uploads/{project_id}/{upload_id}.{ext}                 (api)
/data/cache/tiles/{z}/{x}/{y}.png                            (api)
/data/results/{project_id}/{study_id}/{job_id}/              (solver)
    manifest.json  fields.npz  fields/K.f32 ux.f32 uy.f32 [uz.f32] speed.f32 ti.f32 mask.u8
    images/k.png speed.png zones.png  [viewer3d.json slices/*.f32]  log.txt
/data/results/{project_id}/{study_id}/aggregate/{lawson_hash}/  (solver)
/data/exports/{export_id}.png                                (solver)
/data/reports/{report_id}.pdf                                (solver)
```

### Formato de los campos

- Binario crudo little-endian en orden de filas: float32, o uint8 para las máscaras.
- La forma está en `manifest.json` y en `results.output_grid`.
- La `api` los envía tal cual (`GET /results/{id}/fields/{name}`) con las cabeceras `X-Field-Shape` y `X-Field-Dtype`, y compresión GZip del middleware.
- El navegador construye un `Float32Array` directamente, sin parseo.
- `fields.npz` agrupa todo para la descarga.

### Escrituras

El `solver` escribe en un directorio `*.tmp` y lo renombra al terminar, de forma atómica. Así la `api` nunca lee resultados a medias.

### Borrado

- La `api` borra `/data/results/{project_id}` y `/data/uploads/{project_id}` cuando se elimina un proyecto.
- La purga de retención borra los directorios de los trabajos fallidos.

## Alternativas rechazadas

- **Campos en Postgres (`bytea` o `large objects`).** Hincharían la base, el vacuum sería costoso y no se podrían servir sin copia.
- **Almacenamiento de objetos (MinIO).** Un servicio más sin ninguna necesidad que lo justifique.
- **Bind mounts.** Problemas de rutas y permisos en Windows. Incumplen NFR-12.
- **Dos volúmenes separados (`uploads` y `results`).** Más configuración sin aislamiento real: ambos servicios necesitan acceso.

## Consecuencias

Positivas:

- Transferencia directa al navegador.
- Exportación simple.
- Copia de seguridad trivial con `docker volume`.

Negativas y riesgos:

- `api` y `solver` comparten UID. Una incoherencia rompe los permisos, y lo vigila una prueba de humo (OPS-11).
- El volumen crece con los resultados. `reset` lo borra y la eliminación de proyectos lo limpia.

Qué debe hacer cada paquete de trabajo:

- **WP-API** y **WP-SOLVER:** UID 10001 y las rutas exactas del contrato.
- **WP-OPS:** declara ambos volúmenes con nombre en `compose.yaml`.
