# ADR-05 — Descubrimiento de la api por la SPA: puertos persistidos y `config.json` en tiempo de ejecución

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Los puertos publicados al host los asigna el kernel en tiempo de ejecución (`nexcraft-conventions/ports.md`). En los equipos de desarrollo, 3000 y 8000 suelen estar ocupados. Requisitos de la historia US-15 y de FR-06:

- Si un puerto está ocupado, se asigna otro y se imprime el efectivo.
- El script imprime la URL y abre el navegador.

La SPA corre en el navegador y debe conocer la URL pública de la `api`. Hay tres limitaciones:

- Las variables `VITE_*` se resuelven al compilar.
- `serve` no puede hacer de proxy.
- nginx está prohibido.

## Decisión

### Puertos

En `compose.yaml` los puertos se publican así:

- `web`: `127.0.0.1:${RAFAGA_WEB_PORT:-0}:3000`
- `api`: `127.0.0.1:${RAFAGA_API_PORT:-0}:8000`

Con la variable vacía, el kernel elige el puerto. Solo se escucha en loopback (ADR-25).

### Flujo del script `start` (WP-OPS, `scripts/rafaga.sh` y `scripts/rafaga.ps1`)

1. Verifica `docker`, `docker compose` v2 y el demonio (`docker info`).
2. Si no existe `.env`, lo crea desde `.env.example` y genera los secretos (ADR-06, ADR-25). `RAFAGA_WEB_PORT` y `RAFAGA_API_PORT` quedan vacíos.
3. Detecta y prueba la GPU (ADR-17) y decide la lista de archivos compose.
4. Ejecuta `docker compose up -d --build`.
5. Si `up` falla con `port is already allocated` o `address already in use`, vacía en `.env` los puertos persistidos y reintenta una vez. Así el kernel asigna otros.
6. Lee los puertos efectivos con `docker compose port web 3000` y `docker compose port api 8000`, y extrae el número tras el último `:`.
7. Si los valores de `.env` estaban vacíos o difieren de los efectivos, escribe `RAFAGA_WEB_PORT` y `RAFAGA_API_PORT` en `.env` y vuelve a ejecutar `docker compose up -d`. Esto recrea `api` (cambia `ALLOWED_ORIGINS`) y `web` (cambia `RAFAGA_API_PORT`) con esos mismos puertos, ya fijados. Si en esa pequeña ventana otro proceso tomó el puerto, se repite el paso 5, como máximo tres intentos.
8. Espera a que `http://127.0.0.1:<api>/health` responda 200 y a que `http://127.0.0.1:<web>/` también lo haga. El tiempo límite es de 600 s en el primer arranque (incluye la construcción de imágenes) y de 180 s en los siguientes.
9. Imprime `Ráfaga está lista en http://localhost:<web>` y el dispositivo (GPU o CPU), y abre el navegador.

En los arranques siguientes se reutilizan los puertos persistidos, de modo que la URL es estable y se puede guardar en marcadores.

### `config.json` en tiempo de ejecución

El `docker-entrypoint.sh` (POSIX sh) de la imagen `web` escribe `dist/config.json` a partir de `RAFAGA_API_PORT` y después ejecuta `exec serve -s dist -l tcp://0.0.0.0:3000`. El contenido es:

```json
{"apiPort": 49231, "apiBaseUrl": null}
```

- `apiBaseUrl` es un override avanzado (por ejemplo, `http://127.0.0.1:8000`). Si no es `null`, tiene prioridad.
- `serve.json` declara `Cache-Control: no-store` para `/config.json`.
- `dist/` pertenece al usuario `node`, así que el entrypoint puede escribir sin root.

### Comportamiento de la SPA (WEB-01)

- Antes de montar el router, hace `fetch('/config.json', {cache: 'no-store'})`.
- Construye la base como `${location.protocol}//${location.hostname}:${apiPort}/api/v1`. Así funcionan tanto `localhost` como `127.0.0.1`.
- `ALLOWED_ORIGINS` contiene las dos formas, y `compose.yaml` las construye desde `RAFAGA_WEB_PORT`.
- Si la configuración falta o no es válida, la SPA muestra «No se encuentra el servicio. Ejecuta start de nuevo.».

## Alternativas rechazadas

- **`VITE_API_URL` como build arg.** Habría que reconstruir la imagen cada vez que cambia el puerto, y en el primer arranque el puerto no se conoce antes de construir.
- **nginx u otro proxy inverso.** Está prohibido por las convenciones: añade un proceso root y un segundo lenguaje de configuración.
- **Que la `api` sirva la SPA.** Está prohibido: el backend nunca sirve los estáticos del frontend.
- **Puertos fijos 3000 y 8000.** Chocan con otros servicios en la máquina del usuario.
- **Que el script busque un puerto libre y luego lo enlace.** Tiene una carrera TOCTOU. El kernel es el único que elige y enlaza en un solo paso.
- **Escribir `config.json` con `docker compose cp` o `exec` después de arrancar.** Es frágil y se pierde al recrear el contenedor.

## Consecuencias

Positivas:

- La URL es estable entre reinicios.
- Un puerto ocupado se resuelve automáticamente.
- No hace falta reconstruir para cambiar de puerto.
- La SPA no lleva URL compilada.

Negativas y riesgos:

- Quien ejecute `docker compose up` sin el script, en el primer arranque, obtiene puertos aleatorios y un `config.json` con `apiPort` 0. El README indica que se use siempre `start`, o que se fijen los puertos a mano en `.env`.
- Se desvía de la regla genérica «VITE_* como build args». No existe ninguna variable `VITE_API_URL`, y esta desviación queda registrada aquí.

Qué debe hacer cada paquete de trabajo:

- **WP-OPS:** implementa los pasos 1-9 en sh y PowerShell.
- **WP-WEB:** implementa el entrypoint, `serve.json` y WEB-01.
- **WP-API:** lee `ALLOWED_ORIGINS` como una lista separada por comas.
