# ADR-26 — Valores de límite de peticiones

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos y convenciones:

- **NFR-14:** límite de peticiones.
- **Canon de ingeniería y `fastapi-senior`:** límite en dos niveles, antes de la autenticación por dirección y después por principal, con valores decididos y no por defecto.

Patrones de tráfico reales de la SPA:

- Sondeo de progreso a 1 Hz (ADR-07).
- MapLibre pide decenas de teselas por paneo (ADR-09).
- Exportaciones y campos binarios a ráfagas.

El inicio de sesión es la superficie de fuerza bruta. Hay una sola réplica de la `api`.

## Decisión

| Nivel | Clave | Variable | Valor | Ámbito |
|---|---|---|---|---|
| 1 (antes de autenticar) | dirección del cliente (IPv6 por /64) | `RATE_LIMIT_ANON_PER_MINUTE` | 120 | Todas las rutas salvo `/health` |
| Inicio de sesión | dirección | `RATE_LIMIT_LOGIN_PER_MINUTE` | 10 | `POST /auth/login`, `POST /auth/setup` |
| 2 (después de autenticar) | id de usuario | `RATE_LIMIT_PER_MINUTE` | 600 | Rutas autenticadas salvo teselas |
| Teselas | id de usuario | `RATE_LIMIT_TILES_PER_MINUTE` | 1500 | `GET /tiles/{z}/{x}/{y}.png` |

### Peticiones de teselas antes de autenticar

El nivel 1 de 120/min se aplicaría también a las teselas, porque cuenta todas las peticiones antes de autenticar. Para no estrangular los paneos, las rutas `/api/v1/tiles/*` tienen un presupuesto de nivel 1 propio de 1500/min por dirección.

Es razonable porque solo responden a usuarios con token válido: el coste para un atacante sin token es un 401 barato.

### Comportamiento común

- `TRUST_PROXY=false`: la dirección es la del socket, ya que no hay proxy.
- `/health` está exento de todos los niveles.
- Cualquier exceso responde 429 con `Retry-After` y el cuerpo de error común `rate_limited`.
- El almacén es en memoria (`limits` con `memory://`), suficiente con una réplica. Antes de una segunda réplica habría que nombrar un almacén compartido.
- La clave nunca es la cabecera de credenciales en crudo.

### Cálculo de holgura

- Una pestaña con un estudio activo hace ~60 peticiones/min de sondeo y ~20 de navegación.
- Con 3 pestañas o usuarios (A-11) son ~240/min, por debajo de 600.
- Un paneo rápido ronda las 100–300 teselas por minuto.

## Alternativas rechazadas

- **Valores por defecto de la skill (120/60).** El sondeo de 1 Hz agota 60/min por sí solo y produciría 429 durante un uso normal.
- **Sin límite por ser local.** Incumple NFR-14 y el canon, y deja abierta la fuerza bruta contra el inicio de sesión desde otras pestañas o procesos.
- **Almacén Redis compartido.** No hace falta con una sola réplica, y Redis está excluido.

## Consecuencias

Positivas:

- El uso normal no se ve afectado.
- La fuerza bruta del inicio de sesión queda limitada a 10 intentos por minuto.

Negativas y riesgos:

- Los contadores se reinician con la `api`, lo que es aceptable en local.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** `security/rate_limit`, con pruebas de 429 por nivel y de la exención de `/health`.
- **WP-WEB:** muestra el tiempo de espera de `Retry-After` en SCR-02 y aplica reintentos con espera en las consultas.
- **WP-OPS:** declara las variables en `.env.example`.
