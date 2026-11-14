# ADR-06 — Cuentas locales, JWT bearer y creación de cuenta en el primer arranque

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Requisitos que debe cumplir la autenticación:

- **FR-01 y US-01:** pantalla de creación de cuenta local cuando no existe ningún usuario.
- **FR-02:** autenticación por token en todas las rutas salvo `/health`.
- **FR-03 y US-16:** roles arquitecto y revisor.
- **NFR-14:** hash Argon2 o bcrypt y aislamiento sin IDOR.
- **FR-08:** secretos generados en el primer arranque.
- **US-10:** recargar la página conserva el progreso, así que la sesión debe sobrevivir a la recarga.

La SPA y la `api` están en puertos distintos de `localhost`, por lo que son orígenes distintos.

## Decisión

- **Hash.** argon2id con los parámetros por defecto de `argon2-cffi`.
- **Token.**
  - JWT HS256 firmado con `JWT_SECRET`: 64 bytes aleatorios en base64url, generados por `start`.
  - Claims: `sub` (id de usuario), `role`, `iat`, `exp` y `jti`.
  - Vigencia de `JWT_TTL_MINUTES=720` (12 h).
  - Se envía como `Authorization: Bearer`.
- **Almacenamiento en la SPA.** El token va en `sessionStorage`: sobrevive a la recarga y desaparece al cerrar la pestaña. No hay cookies.
- **Rutas públicas** (`PUBLIC_PATHS`): `/health`, `/api/v1/auth/setup-status`, `/api/v1/auth/setup` y `/api/v1/auth/login`. Una prueba estructural verifica que cualquier otra ruta resuelve un guard `require_*`.
- **Creación de cuenta.**
  - `POST /auth/setup` toma `pg_advisory_xact_lock` y cuenta los usuarios.
  - Si hay cero, crea un `architect` y devuelve el token (201).
  - Si ya hay alguno, devuelve 409 `setup_already_done`.
  - Contraseña de ≥10 caracteres; si no, 422 `password_too_short`.
- **Semilla opcional.** Si `ADMIN_EMAIL` y `ADMIN_PASSWORD` no están vacías, el arranque inserta un arquitecto solo si ese correo no existe. Nunca sobrescribe una contraseña existente.
- **Inicio de sesión.** Un correo desconocido y una contraseña errónea devuelven el mismo cuerpo 401 `invalid_credentials`. Hay un límite de 10 intentos por minuto y dirección (ADR-26).
- **Roles.**
  - `architect`: lectura y escritura, gestiona usuarios y comparte proyectos.
  - `reviewer`: solo lectura en los proyectos compartidos con él. Cualquier escritura o lanzamiento devuelve 403 `forbidden`.
  - Un proyecto ajeno sin compartir devuelve 404, con cuerpo idéntico al de un id inexistente.

## Alternativas rechazadas

- **Sesión por cookie.** La `api` y la `web` son orígenes distintos. Exigiría CORS con credenciales, decisiones de SameSite y protección CSRF, todo sin beneficio para una app local.
- **Sin autenticación en localhost.** Incumple FR-02. Además, cualquier pestaña del navegador podría llamar a la API.
- **OAuth u OIDC.** Requiere un proveedor de identidad externo, lo que es incompatible con una instalación local sin red.
- **Token en `localStorage`.** Persistiría indefinidamente entre sesiones, y una pestaña compartida heredaría la sesión. `sessionStorage` cumple US-10 con menos exposición.

## Consecuencias

Positivas:

- No hay riesgo de CSRF.
- El estado del servidor es mínimo.
- La creación de cuenta es segura frente a carreras de concurrencia.

Negativas y riesgos:

- Un token comprometido sigue siendo válido hasta 12 h, porque no hay lista de revocación. Es aceptable en un entorno local de un solo puesto.
- Cambiar `JWT_SECRET` invalida todas las sesiones.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** módulos `security/jwt`, `security/passwords` y `security/ownership`, más las pruebas de cuerpos 404 idénticos byte a byte.
- **WP-WEB:** SCR-01 y SCR-02, guard de rutas y gestión del 401 (vuelta al inicio de sesión).
- **WP-OPS:** genera `JWT_SECRET` sin imprimirlo.
