# ADR-25 — Distribución: scripts start, stop y reset, secretos y enlace a loopback

Estado: Aceptada
Fecha: 2026-11-13

> Enmienda (2026-11-13, ADR-29): las imágenes de registro dejan de estar fuera de alcance como opción. `RAFAGA_IMAGE_REGISTRY` vacía (por defecto) mantiene la construcción local.

## Contexto

Requisitos de distribución:

- **FR-06:** `start` en Linux y Windows.
- **FR-07:** `stop` conserva los datos y `reset` los borra con confirmación.
- **FR-08:** los secretos se generan sin imprimirlos.
- **FR-10:** README en español.
- **NFR-09 a NFR-12:** instalación en ≤15 min, Linux y Windows, volúmenes con nombre y LF en `.sh`.
- **OOS-6:** uso local, no remoto.
- **OOS-9:** sin registry de imágenes.
- **BG-4:** un solo comando.

## Decisión

### Puntos de entrada en la raíz

| Linux | Windows | Implementación |
|---|---|---|
| `./start.sh` | `start.bat` o `start.ps1` | `scripts/rafaga.sh start`, `scripts/rafaga.ps1 start` |
| `./stop.sh` | `stop.bat` o `stop.ps1` | `… stop` |
| `./reset.sh` | `reset.bat` o `reset.ps1` | `… reset` |

Los `.bat` ejecutan `powershell -NoProfile -ExecutionPolicy Bypass -File <x>.ps1` y hacen una pausa si hay error, para que funcionen con doble clic. La lógica vive en un solo script por plataforma, con funciones de ≤30 líneas.

### `compose.yaml`

- `name: rafaga`, así que `docker compose -p rafaga …` funciona desde cualquier directorio.
- Puertos publicados solo en `127.0.0.1` (ADR-05). `solver` y `db` no se publican.

### `start`

Implementa el flujo de ADR-05 y ADR-17. En el primer arranque genera:

- `POSTGRES_PASSWORD`: 32 bytes en base64url.
- `JWT_SECRET`: 64 bytes en base64url.

Las fuentes de aleatoriedad son `/dev/urandom` en Linux y `System.Security.Cryptography.RandomNumberGenerator` en PowerShell. Se escriben en `.env` y nunca se imprimen ni aparecen en los logs. Si `.env` ya existe, no se tocan.

El script imprime la URL, el dispositivo (GPU o CPU) y cómo detener la aplicación, y abre el navegador con `xdg-open` en Linux o `Start-Process` en Windows.

### Ayudas y errores

- Sin Docker, el script muestra un mensaje con el enlace de instalación (Docker Engine para Linux, Docker Desktop para Windows) y sale con código 1.
- Con el demonio detenido, muestra «Inicia Docker Desktop y vuelve a ejecutar start».

### `stop`

`docker compose -p rafaga stop`. Conserva los volúmenes y `.env`.

### `reset`

Explica qué se borrará y pide escribir `borrar`. Después:

- Ejecuta `docker compose -p rafaga down -v --remove-orphans`.
- Vacía `RAFAGA_WEB_PORT` y `RAFAGA_API_PORT` en `.env`, pero conserva los secretos.

Cualquier otra respuesta aborta sin cambios.

### Archivos de repositorio

- `.gitattributes`: `*.sh` y `docker-entrypoint.sh` con `eol=lf`; `*.bat` y `*.ps1` con `eol=crlf`.
- `.gitignore`: incluye `.env`.
- `.env.example`: valores por defecto documentados, sin secretos y sin ninguna ubicación.

### Prueba de humo

`scripts/smoke.sh` (OPS-11) valida la pila completa con valores sintéticos.

## Alternativas rechazadas

- **Instaladores nativos (MSI, deb).** Empaquetado por sistema operativo y mantenimiento doble. Docker ya es el requisito único (C-1).
- **Imágenes en un registry.** Fuera de alcance (OOS-9). Se podrían añadir más adelante sin cambiar los scripts.
- **Enlazar en 0.0.0.0.** Expondría la app y la API a la red local, en contra de OOS-6.
- **Un Makefile.** No existe de forma nativa en Windows.
- **Pedir los secretos al usuario.** Añade fricción e incumple FR-08.

## Consecuencias

Positivas:

- Un comando por sistema operativo, sin configuración manual.
- La app no es accesible desde fuera del equipo.

Negativas y riesgos:

- Hay dos implementaciones (sh y PowerShell) que deben comportarse igual. La prueba de humo y una lista de comprobación manual en Windows (NFR-10) lo controlan.
- Ejecutar `docker compose` a mano sin `.env` falla con un mensaje claro, porque `POSTGRES_PASSWORD` se marca como obligatoria con `${POSTGRES_PASSWORD:?…}`.

Qué debe hacer cada paquete de trabajo:

- **WP-OPS:** OPS-01 a OPS-11.
