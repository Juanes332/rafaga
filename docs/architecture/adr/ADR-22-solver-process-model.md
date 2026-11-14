# ADR-22 — Modelo de procesos del solver: supervisor, carril pesado y carril ligero

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos del modelo de procesos:

- **US-09:** cancelar en ≤10 s.
- **NFR-13:** un trabajo fallido no afecta a los demás.
- **NFR-19:** `/health` por servicio, con el dispositivo.
- **NFR-05:** recálculo y exportaciones no deben esperar detrás de un 3D.

La memoria GPU de CuPy solo se libera de forma fiable al terminar el proceso. El `solver` está ligado a `fastapi-senior`, con la única ruta `/health`.

## Decisión

### Proceso principal

`uvicorn` con la app FastAPI (`/health`), cuyo `lifespan` arranca el supervisor:

- Una conexión `LISTEN rafaga_jobs` y un sondeo de respaldo cada 2 s.
- Un hilo de latido que hace upsert en `solver_nodes` cada 5 s: dispositivo, `gpu_name`, VRAM, presupuesto de RAM, núcleos, MLUPS y versión.
- La recuperación de huérfanos al arrancar (SOL-04).

### Carril pesado (`lane='heavy'`)

Ejecuta `plan2d`, `section2d` y `volume3d`, como máximo uno a la vez.

- Cada trabajo corre en un proceso hijo creado con `multiprocessing` en modo `spawn`, para que CUDA quede limpio.
- El hijo envía el progreso por una `Queue`, como `(progress, phase, eta)` a ≤1 Hz. El supervisor lo escribe en la fila `jobs` y comprueba `cancel_requested` en cada ciclo.
- **Cancelación:**
  - El supervisor activa un `Event` compartido. El hijo lo revisa cada ≤1 s (cada N pasos calibrados por MLUPS) y sale de forma limpia.
  - Si a los 8 s sigue vivo, recibe `terminate()` y, a los 9 s, `kill()`.
  - El estado pasa a `cancelled` y el directorio temporal se borra.
- Un fallo del hijo (código de salida ≠ 0, OOM o excepción) marca el trabajo como `failed`, con el `error_code` que el hijo haya enviado o con `solver_crashed`. El supervisor sigue funcionando.

### Carril ligero (`lane='light'`)

Ejecuta `aggregate`, `render` y `report` en `LIGHT_LANE_CONCURRENCY=2` hilos, solo en CPU.

Son trabajos de segundos, así que la cancelación es cooperativa entre etapas.

### `/health`

Devuelve `{status, device, gpu_name, db, lanes:{heavy:{busy, job_id}, light:{busy}}}`. Responde 503 si la base de datos no está accesible.

Nunca se bloquea, porque el cómputo ocurre en el hijo o en hilos que liberan el GIL.

### Identidad

`worker_id = hostname + pid + arranque`. Lo usan las filas de `jobs` y la recuperación de huérfanos.

## Alternativas rechazadas

- **Todo en hilos del proceso principal.** No se puede forzar la liberación de la memoria GPU ni matar un kernel colgado, y una excepción nativa tumbaría `/health`.
- **Un proceso hijo persistente para todos los trabajos pesados.** Arrastraría fragmentación del pool de CuPy entre trabajos.
- **Un servicio o contenedor por tipo de trabajo.** Más imágenes y más configuración de GPU. El usuario pidió un solo servicio `solver`.
- **Celery o RQ workers.** Requieren un broker (ADR-02).

## Consecuencias

Positivas:

- La cancelación es garantizada en ≤10 s.
- El aislamiento ante fallos es real.
- Exportaciones y Lawson funcionan mientras corre un 3D.

Negativas y riesgos:

- El arranque de un proceso `spawn` con CuPy cuesta ~1–2 s por trabajo, lo que es despreciable.
- Con 16 direcciones en 2D, la ejecución es secuencial en GPU. Es aceptable porque cada una dura menos de 2 min.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** SOL-01 a SOL-05, con pruebas de cancelación (temporizada) y de fallo del hijo.
- **WP-API:** no envía señales al `solver`. Toda la coordinación pasa por la tabla `jobs`.
