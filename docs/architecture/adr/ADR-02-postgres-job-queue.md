# ADR-02 — Postgres como cola de trabajos

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Los trabajos de simulación, agregación, render e informe se encolan desde la `api` y los consume el `solver`. La cola debe cumplir varios requisitos:

- Estados en cola, ejecutando, completado, fallido y cancelado (FR-39).
- Cancelación en ≤10 s (US-09).
- Progreso visible al menos cada 2 s (NFR-06).
- Recuperación tras reinicio, con los trabajos interrumpidos en «fallido/reanudable» (NFR-13).
- Persistencia entre reinicios (FR-05).

El usuario fijó que no habría Redis.

## Decisión

La tabla `jobs` de Postgres es la cola. Las columnas exactas están en `contracts/job-contract.md` §2.2.

- **Encolado transaccional.** `POST /api/v1/simulations` inserta el `study` y sus N `jobs` en una transacción. Un trigger `AFTER INSERT` ejecuta `pg_notify('rafaga_jobs', lane)`.
- **Reclamo** por carril (`heavy` / `light`):

```sql
UPDATE jobs SET status='running', worker_id=$1, started_at=now(),
       heartbeat_at=now(), attempts=attempts+1
WHERE id = (SELECT id FROM jobs
            WHERE status='queued' AND lane=$2 AND NOT cancel_requested
            ORDER BY priority DESC, created_at
            FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING *;
```

- **Despertar.** El `solver` hace `LISTEN rafaga_jobs` y, como respaldo, sondea cada 2 s por si se pierde una notificación.
- **Progreso.** El `solver` actualiza `progress`, `phase`, `eta_seconds` y `heartbeat_at` aproximadamente cada 1 s. La SPA lo lee por sondeo (ADR-07).
- **Cancelación.** La `api` marca directamente como `cancelled` los trabajos `queued`. Para los `running` pone `cancel_requested=true`, y el `solver` los cierra en ≤10 s (ADR-22).
- **Recuperación.** Al arrancar el `solver`, los trabajos `running` con `heartbeat_at` de más de 60 s pasan a `failed`, con `error_code='worker_restarted'` y `resumable=true`. `POST /jobs/{id}/retry` los vuelve a encolar.
- **Índice parcial:** `(lane, priority DESC, created_at) WHERE status='queued'`.

## Alternativas rechazadas

- **Redis + RQ o Celery.** Añade un servicio y dos fuentes de verdad (estado en Redis y estado de negocio en Postgres). La reconciliación tras un reinicio queda en manos del desarrollador. Además, el usuario lo descartó.
- **RabbitMQ.** Es aún más pesado y no guarda progreso consultable. El progreso tendría que vivir de todos modos en Postgres.
- **Cola en memoria del solver.** Se pierde al reiniciar (incumple NFR-13) y la `api` no podría ver el estado.

## Consecuencias

Positivas:

- Hay un componente menos.
- Se encola y se crea el estudio de forma atómica.
- La interfaz, la cancelación y el progreso leen la misma fila.
- La recuperación es una consulta SQL.

Negativas y riesgos:

- Escribir el progreso cada segundo genera tuplas muertas. Es poco volumen (pocos trabajos activos) y lo cubre el autovacuum.
- `LISTEN` necesita una conexión dedicada en el `solver`.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** crea la tabla, los índices y el trigger NOTIFY en Alembic, e implementa cancelar y reintentar.
- **WP-SOLVER:** usa exactamente la sentencia de reclamo anterior (§4 del contrato). Debe tener una prueba con dos supervisores que demuestre que no hay doble reclamo.
