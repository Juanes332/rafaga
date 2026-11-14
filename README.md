# Ráfaga

Aplicación local para el análisis del viento urbano a escala peatonal (cribado con el método de Boltzmann en malla, LBM). Funciona en tu propio equipo: se instala con un solo comando y no necesita cuenta en ningún servicio.

> **Aviso importante.** Ráfaga es una herramienta de **cribado** para comparar alternativas de diseño en fases tempranas. **No es una certificación** ni sustituye un estudio de túnel de viento o de CFD validado, ni una norma de confort aplicable a un permiso. Los resultados dependen de la geometría, del viento y de la resolución elegidos; interprétalos con criterio profesional.

## Qué incluye

Cuatro contenedores Docker: `web` (interfaz), `api` (servicio principal), `solver` (cálculo, CPU o GPU NVIDIA) y `db` (PostgreSQL). Solo `web` y `api` se publican, **únicamente en `127.0.0.1`** (tu propio equipo); el solver y la base de datos no son accesibles desde fuera de Docker.

## Requisitos de hardware

| Nivel | CPU | RAM disponible para Docker | Alcance |
|---|---|---|---|
| Mínimo | 4 núcleos | 8 GB | Solo 2D; el 3D se ofrece con un límite de 1,5 M nodos y un aviso |
| Recomendado sin GPU | 16 núcleos | 32 GB | 2D completo; 3D reducido (hasta 3 M nodos) |
| Recomendado con GPU | 8 o más núcleos | 16 GB, más una GPU NVIDIA de 8 GB | Todo, incluido el 3D de hasta unos 28 M nodos |

Además: unos 8 GB libres en disco para las imágenes (la del solver ocupa ~2,6 GB: incluye solo las bibliotecas CUDA que usa, runtime, NVRTC y cuBLAS) y conexión a internet en la primera instalación. La GPU es opcional: sin ella, Ráfaga usa la CPU automáticamente.

## Instalación en Linux (Docker Engine)

1. **Instala Docker Engine y el plugin Compose v2**: <https://docs.docker.com/engine/install/> (el plugin `docker compose` viene incluido en las instrucciones oficiales). Comprueba con `docker compose version`.
2. **Permite usar Docker sin `sudo`**: `sudo usermod -aG docker $USER`, cierra sesión y vuelve a entrar.
3. **(Solo con GPU NVIDIA)**
   1. Instala el driver propietario de NVIDIA (versión 535 o superior). `nvidia-smi` debe funcionar.
   2. Instala el NVIDIA Container Toolkit: <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html>
   3. Configura Docker: `sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`
   4. Comprueba: `docker run --rm --gpus all ubuntu nvidia-smi` debe mostrar tu GPU.
4. **Obtén el proyecto** (clona el repositorio o descomprime el archivo) y entra en la carpeta.
5. **Arranca**: `./start.sh`

La primera vez construye las imágenes (varios minutos). Al terminar verás `Ráfaga está lista en http://localhost:<puerto>` y se abrirá el navegador. Si el archivo no es ejecutable: `chmod +x start.sh stop.sh reset.sh scripts/*.sh`.

## Instalación en Windows (Docker Desktop + WSL2)

1. **Activa WSL2**: abre PowerShell como administrador y ejecuta `wsl --install`; reinicia el equipo. Después, `wsl --update`.
2. **Instala Docker Desktop**: <https://docs.docker.com/desktop/setup/install/windows-install/>. Durante la instalación deja marcada la opción **Use WSL 2 instead of Hyper-V**. Abre Docker Desktop y espera a que indique que está en marcha.
3. **(Solo con GPU NVIDIA)**
   1. Instala el driver NVIDIA de **Windows** (versión 535 o superior) desde <https://www.nvidia.com/drivers>. **No instales ningún driver dentro de WSL**: WSL2 usa el de Windows.
   2. En Docker Desktop: Settings, General, marca **Use the WSL 2 based engine**.
   3. Comprueba en PowerShell: `nvidia-smi` y `docker run --rm --gpus all ubuntu nvidia-smi`.
4. **(Recomendado) Sube la memoria de WSL2.** Por defecto Docker usa el 50 % de la RAM. Crea o edita `%UserProfile%\.wslconfig`:

   ```
   [wsl2]
   memory=24GB
   ```

   y reinicia WSL con `wsl --shutdown` (luego reabre Docker Desktop). Ajusta el valor a tu equipo, dejando RAM al sistema.
5. **Obtén el proyecto** (descomprime el archivo o clona el repositorio) en una carpeta de tu disco.
6. **Arranca**: doble clic en `start.bat` (o, en PowerShell, `powershell -ExecutionPolicy Bypass -File .\start.ps1`: la política por defecto de Windows bloquea los `.ps1` sueltos). Si Windows muestra un aviso de SmartScreen, elige "Más información" y "Ejecutar de todos modos".

La primera vez tarda varios minutos. Verás `Ráfaga está lista en http://localhost:<puerto>` y se abrirá el navegador.

## Imágenes prediseñadas (opcional)

Por defecto `start` **construye** las imágenes en tu equipo. Si quien mantiene la instalación publica las imágenes en un registro, puedes descargarlas en vez de construir (más rápido y sin compilar nada). En `.env`:

```
RAFAGA_IMAGE_REGISTRY=ghcr.io/mi-organizacion
RAFAGA_VERSION=1.0.0
```

`start` ejecutará `docker compose pull` de `<registro>/rafaga-api`, `rafaga-solver` y `rafaga-web` con esa versión (`1.0.0` si no indicas `RAFAGA_VERSION`, ADR-29: nunca `latest`; si la descarga falla, el script avisa y construye en local) y arrancará sin construir. Si el registro es privado, haz antes `docker login`. Con `RAFAGA_IMAGE_REGISTRY` vacío (valor por defecto) todo se construye en local. Para publicar las imágenes: `docker compose build`, luego `docker tag rafaga-solver:1.0.0 <registro>/rafaga-solver:<versión>` y `docker push` (igual con `api` y `web`).

## Uso diario

| Acción | Linux | Windows |
|---|---|---|
| Arrancar | `./start.sh` | `start.bat` |
| Detener (conserva los datos) | `./stop.sh` | `stop.bat` |
| Borrar todos los datos | `./reset.sh` | `reset.bat` |

- Usa **siempre `start`** y no `docker compose up` a mano: el script genera los secretos, elige los puertos libres, comprueba la GPU y espera a que todo esté listo. Si prefieres lanzar compose tú, fija `RAFAGA_WEB_PORT` y `RAFAGA_API_PORT` en `.env` antes.
- El primer arranque asigna puertos libres y los guarda en `.env`; la dirección (`http://localhost:<puerto>`) se mantiene en los arranques siguientes, así que puedes guardarla en marcadores. Si un puerto guardado se ocupa, se elige otro solo.
- **Primer uso:** la pantalla inicial te pide crear la cuenta de arquitecto. No hay ninguna ubicación, ciudad ni dato de viento predefinido.
- `reset` te pide escribir `borrar`; cualquier otra respuesta cancela. Borra proyectos, resultados y cuentas, pero conserva los secretos de `.env`.
- Los datos viven en volúmenes Docker con nombre (`rafaga-db`, `rafaga-data`), no en carpetas del proyecto. Para copia de seguridad usa las herramientas de volúmenes de Docker.

## Privacidad de los datos

Todo se calcula y guarda en tu equipo. Las **únicas** conexiones a internet son:

- **Open-Meteo** (geocodificación, elevación y clima histórico): se envían las coordenadas redondeadas y el texto de búsqueda.
- **OpenStreetMap** (teselas del mapa): se envían las coordenadas de las teselas que ves.

No hay telemetría. Tus geometrías, planos y resultados no salen del equipo. Los secretos (`POSTGRES_PASSWORD`, `JWT_SECRET`) se generan en `.env`, nunca se imprimen y no deben subirse al repositorio.

## Solución de problemas

**Docker no está instalado / Compose v2 ausente.** El script lo indica con el enlace. Comprueba `docker compose version`.

**"Docker no responde" / demonio detenido.** Windows: abre Docker Desktop y espera a que esté en marcha. Linux: `sudo systemctl start docker`.

**"permission denied" al usar Docker (Linux).** `sudo usermod -aG docker $USER`, cierra sesión y vuelve a entrar.

**Puerto ocupado.** El script lo resuelve solo eligiendo otro puerto libre. Si falla repetidamente, cierra programas que usen muchos puertos o ejecuta `stop` y `start` otra vez.

**La construcción falla o es muy lenta.** Revisa internet y el espacio en disco (`docker system df`). Ver registros: `docker compose -p rafaga logs api` (o `solver`, `web`, `db`).

**La página dice "No se encuentra el servicio. Ejecuta start de nuevo."** Se lanzó la pila sin el script o los puertos cambiaron. Ejecuta `start` de nuevo.

**Se queda esperando y agota el tiempo.** El primer arranque puede tardar hasta 10 minutos; los siguientes, 3. Mira `docker compose -p rafaga ps` y los registros del servicio que no esté `healthy`.

**Se agota la memoria en trabajos grandes (Windows).** Sube `memory` en `.wslconfig` (ver arriba) y ejecuta `wsl --shutdown`.

### GPU no detectada o no utilizable

Si `nvidia-smi` funciona en tu equipo pero el script muestra "GPU NVIDIA no detectada" o "no está disponible dentro de Docker", Ráfaga sigue funcionando en CPU. Para activar la GPU:

- **Driver NVIDIA 535 o superior.** En Windows, es el driver de Windows el que usa WSL2; no instales ninguno dentro de WSL.
- **Windows:** Docker Desktop con el motor WSL 2 activado (Settings, General, "Use the WSL 2 based engine"), WSL actualizado (`wsl --update`, kernel 5.10.43 o superior) y reinicio con `wsl --shutdown`.
- **Linux:** NVIDIA Container Toolkit instalado y configurado: `sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`. Comprueba con `docker run --rm --gpus all ubuntu nvidia-smi`.
- **Mensajes frecuentes:**
  - `could not select device driver "nvidia"`: falta el NVIDIA Container Toolkit (Linux) o el motor WSL 2 (Windows).
  - `CUDA driver version is insufficient`: actualiza el driver NVIDIA.
- Después de corregirlo, vuelve a ejecutar `start`. Puedes forzar el dispositivo con `RAFAGA_DEVICE=cpu` o `gpu` en `.env` (`auto` por defecto).

## Lista de comprobación manual en Windows

Los scripts de Windows (`start.bat`, `stop.bat`, `reset.bat` y `scripts/rafaga.ps1`) se verificaron solo de forma **estática y en un contenedor PowerShell 7 en Linux** (análisis sintáctico, PSScriptAnalyzer y una ejecución con `docker` simulado); **no se han ejecutado en un Windows real**. Antes de darlos por buenos, en un equipo con Windows 10/11 y Docker Desktop (WSL 2):

1. Descomprime el proyecto en una ruta **con espacios** (por ejemplo `C:\Users\tu nombre\Mi carpeta\rafaga`). Comprueba que los `.bat` y `.ps1` conservan finales de línea CRLF y que los `.sh` y `compose.yaml` conservan LF (`.gitattributes` lo fuerza).
2. Con Docker Desktop **cerrado**, doble clic en `start.bat`: debe mostrar «Docker no responde…» en español y esperar una tecla.
3. Abre Docker Desktop y repite: se crea `.env` con `POSTGRES_PASSWORD` y `JWT_SECRET` rellenados, se construye y se abre el navegador en `http://localhost:<puerto>`.
4. Abre `.env`: `RAFAGA_WEB_PORT` y `RAFAGA_API_PORT` tienen valor. Cierra y vuelve a ejecutar `start.bat`: la dirección es la misma y arranca en segundos.
5. Con un programa ocupando el puerto web guardado, ejecuta `start.bat`: debe elegir otro puerto solo.
6. Con GPU NVIDIA: la salida muestra `GPU: <nombre>`; sin GPU o sin el motor WSL 2: `CPU` y un aviso. Con `RAFAGA_DEVICE=cpu` en `.env` debe usar la CPU.
7. Crea la cuenta, lanza una simulación 2D pequeña y comprueba que termina.
8. `stop.bat`: detiene sin borrar datos; `start.bat` de nuevo conserva la cuenta.
9. `reset.bat`: escribe algo distinto de `borrar` (cancela) y luego `borrar` (borra los datos y vacía los puertos de `.env`, conservando los secretos).
10. (Opcional) Pon `RAFAGA_IMAGE_REGISTRY` con un registro de pruebas y comprueba que `start.bat` descarga en vez de construir.
11. Desde `cmd`, con `set RAFAGA_NO_PAUSE=1` y `set RAFAGA_NO_BROWSER=1`, `start.bat` debe terminar sin esperar una tecla ni abrir el navegador.

Anota cualquier fallo con el texto exacto del mensaje. La misma lista, en formato de casillas, está en `docs/ops/windows-checklist.md`; el análisis estático se repite con `scripts/lint-ps.sh` y la caída a construcción local con `scripts/tests/test-pull-fallback.sh`.

## Prueba de humo (para quien mantiene la instalación)

Con la pila en marcha: `scripts/smoke.sh` (requiere `curl` y `python3`). Crea un proyecto con datos sintéticos, dibuja un bloque, ejecuta un plan 2D grueso y comprueba el campo K, el PNG y el PDF. Si ya existe una cuenta, define `SMOKE_EMAIL` y `SMOKE_PASSWORD`.

## Configuración

Todas las variables están documentadas en `.env.example`. `start` crea `.env` a partir de él. No hace falta tocar nada para un uso normal.
