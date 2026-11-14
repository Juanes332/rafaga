# ADR-17 — Verificación de GPU en Linux y Windows/WSL2, y CuPy desde wheels (Q-7)

Estado: Aceptada
Fecha: 2026-11-13

> Enmienda (2026-11-13, ADR-29): `cupy-cuda12x[ctk]` se sustituye por `cupy-cuda12x` más las ruedas `nvidia-cuda-runtime-cu12` y `nvidia-cuda-nvrtc-cu12`, para que la imagen del solver quede en ≤ 3 GB.

## Contexto

Q-7 pide una estrategia de verificación del arranque GPU en Windows/WSL2. Requisitos relacionados:

- **FR-06** y **US-15:** detección de GPU con `nvidia-smi` y aplicación automática de la configuración GPU.
- **FR-38:** respaldo en CPU.
- **NFR-10:** Linux y Windows.
- **NFR-21:** tamaño de las imágenes.
- **A-6:** RTX 4060 con NVIDIA Container Toolkit o soporte CUDA en WSL2.

Un caso frecuente: `nvidia-smi` funciona en el host, pero el runtime de contenedores no expone la GPU. Pasa cuando falta el toolkit en Linux o cuando Docker Desktop no usa el backend WSL2.

## Decisión

### Imagen

`solver` usa `python:3.12-slim`, resuelto vía `runtimes.yaml`, con `pip install cupy-cuda12x[ctk]`.

- El extra `ctk` trae las wheels de NVIDIA (runtime, NVRTC y cuBLAS).
- No hace falta una imagen base `nvidia/cuda`.
- El driver lo aporta el host.
- Sin GPU, el import de CuPy falla de forma controlada y se usa NumPy.

### Sonda dentro del contenedor

`python -m app.services.device.device_probe`:

1. Importa cupy.
2. Comprueba que `cupy.cuda.runtime.getDeviceCount() ≥ 1`.
3. Reserva 64 MiB.
4. Compila y ejecuta un `RawKernel` trivial (suma de vectores) y verifica el resultado.
5. Imprime un JSON `{ok, gpu_name, vram_total_bytes, cuda_runtime, driver}` y sale con 0. Cualquier fallo sale con código ≠ 0 y el motivo.

### Flujo en `start` (Linux y Windows por igual)

1. Si `nvidia-smi -L` no existe o falla, se arranca solo con CPU. El script imprime «GPU NVIDIA no detectada: se usará la CPU».
2. Si funciona, se construye la imagen y se ejecuta `docker compose -f compose.yaml -f compose.gpu.yaml run --rm --no-deps solver python -m app.services.device.device_probe`.
3. Con salida 0, se mantiene `compose.gpu.yaml` en todos los comandos de esta ejecución y se imprime «GPU: <modelo>».
4. Con salida ≠ 0, se avisa con el motivo y el enlace a la sección del README, y se arranca solo con CPU. Nunca se aborta.

En tiempo de ejecución, el `solver` repite la sonda al arrancar y publica el dispositivo en `solver_nodes`. `RAFAGA_DEVICE` (auto, cpu o gpu) y el `device` de cada trabajo permiten forzar el dispositivo (FR-56). Si se pide GPU y no hay, el trabajo falla con `device_unavailable`.

### Solución de problemas en el README

- **Driver NVIDIA ≥ R535**, en Windows: el driver de Windows es el que usa WSL2. No se instala ningún driver dentro de WSL.
- **Windows:** Docker Desktop con el backend WSL2 activado (Settings, General, «Use the WSL 2 based engine»), WSL actualizado con `wsl --update`, kernel ≥ 5.10.43 y reinicio con `wsl --shutdown`.
- **Linux:** NVIDIA Container Toolkit instalado y `sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`. Comprobación con `docker run --rm --gpus all ubuntu nvidia-smi`.
- **Síntomas habituales y su causa:**
  - `could not select device driver "nvidia"` indica que falta el toolkit.
  - `CUDA driver version is insufficient` indica que hay que actualizar el driver.

## Alternativas rechazadas

- **Fiarse solo de `nvidia-smi` en el host.** Daría falsos positivos cuando el runtime de contenedores no está configurado, y el usuario vería fallar el primer trabajo.
- **Imágenes base `nvidia/cuda:*-runtime`.** Añaden más de 3 GB, no se resuelven por `runtimes.yaml` y complican el usuario no root.
- **Dos imágenes de solver (CPU y GPU).** Más construcción y más superficie. La misma imagen funciona en ambos modos.
- **Abortar si la sonda falla.** Contradice BR-17: la CPU siempre es válida.

## Consecuencias

Positivas:

- Un único procedimiento en los dos sistemas operativos.
- Los errores se diagnostican antes del primer trabajo.
- Una sola imagen de solver.

Negativas y riesgos:

- La sonda añade ~5–10 s al arranque.
- Las wheels CUDA pesan ~1,5 GB. NFR-21 (≤12 GB en total) se sigue cumpliendo.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** `device_probe` y la selección de dispositivo (SOL-03).
- **WP-OPS:** el flujo en `rafaga.sh`/`rafaga.ps1` y la sección del README.
