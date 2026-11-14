# ADR-07 — Progreso de trabajos por sondeo HTTP

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos que debe cumplir la entrega del progreso:

- **NFR-06:** actualización visible al menos cada 2 s.
- **US-10:** el progreso se recupera tras recargar.
- **FR-39:** estados y cancelación.

La autenticación es con bearer en cabecera (ADR-06). Hay como mucho 3 usuarios locales concurrentes (A-11).

## Decisión

Mientras el estudio tenga algún trabajo `queued` o `running`, la SPA consulta `GET /api/v1/simulations/{study_id}` cada 1 s con TanStack Query, usando `refetchInterval` condicional.

- Cuando todos los trabajos son terminales, el sondeo se detiene.
- La lista de estudios (`GET /projects/{id}/simulations`) se consulta cada 3 s mientras la pantalla de trabajos está visible.
- Los trabajos ligeros (exportaciones e informes) se consultan cada 1 s hasta terminar.

La respuesta incluye `progress`, `phase`, `eta_seconds`, `device_used` y `error` por trabajo, y el `solver` actualiza esos campos cada ~1 s (ADR-02). Con sondeo de 1 s y escritura de 1 s, la latencia máxima percibida es de ~2 s, lo que cumple NFR-06.

## Alternativas rechazadas

- **Server-Sent Events.** `EventSource` no permite cabeceras `Authorization`. Habría que meter el token en la URL, y acabaría en logs e historial. También haría falta un mecanismo de difusión desde Postgres hacia la `api`.
- **WebSocket.** Es otro protocolo que gestionar: autenticación dentro del handler, reconexión y proxys. No se justifica para un puñado de trabajos.
- **Long polling.** Es más complejo que el sondeo y la ganancia de latencia no se necesita.

## Consecuencias

Positivas:

- Sin infraestructura adicional.
- El mismo endpoint sirve para recargar la página y para recuperar el estado.
- Es fácil de probar con MSW.

Negativas y riesgos:

- Unas 60 peticiones por minuto por pestaña activa. El límite por principal se fija en 600/min (ADR-26).
- La respuesta de `GET /simulations/{id}` debe ser barata: lectura indexada por `study_id`, sin abrir ficheros.

Qué debe hacer cada paquete de trabajo:

- **WP-WEB:** sondeo condicional en `api/simulations`.
- **WP-API:** endpoint ligero.
- **WP-SOLVER:** escrituras de progreso limitadas a 1 Hz.
