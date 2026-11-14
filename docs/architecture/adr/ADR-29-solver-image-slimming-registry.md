# ADR-29 — Imagen del solver reducida y descarga opcional desde un registro (BL-05)

Estado: Aceptada
Fecha: 2026-11-13
Enmienda: ADR-17 (ruedas de CuPy) y ADR-25 (imágenes de registro, antes fuera de alcance)

## Contexto

La imagen `rafaga-solver` mide unos 5,5 GB en disco. La mayor parte viene de
`cupy-cuda12x[ctk]`, que instala el toolkit CUDA completo en ruedas (cuBLAS, cuFFT,
cuSOLVER, cuSPARSE, cuRAND, NPP…). El solver solo usa `RawKernel`, elementwise y
reducciones de CuPy: necesita el runtime y NVRTC, nada más. En un portátil, 5,5 GB alargan
el primer `start` y ocupan disco del usuario.

ADR-25 rechazó las imágenes de registro (OOS-9, "opcional más adelante"). Con una imagen
grande, poder descargarla ya construida ahorra la compilación en equipos lentos.

## Decisión

### Reducción de la imagen

- Construcción multietapa sobre `python:3.12-slim` (sin cambios de base, ADR-17).
- En lugar de `[ctk]`, se instalan solo `cupy-cuda12x`, `nvidia-cuda-runtime-cu12` y
  `nvidia-cuda-nvrtc-cu12`, con versiones fijadas en `requirements.txt`. CuPy carga las
  bibliotecas de forma perezosa, así que las no instaladas no se piden mientras no se usen.
- La etapa final no lleva compiladores ni cabeceras; `pip --no-cache-dir`, sin `__pycache__`
  de pruebas y `.dockerignore` que excluye `tests/`, `bench/` de salida y artefactos.
- Objetivo: `docker image inspect -f '{{.Size}}'` ≤ 3 000 000 000 bytes.
- Verificación: la prueba de dispositivo de ADR-17 (un `RawKernel` y una reducción) pasa en
  la imagen reducida bajo `compose.gpu.yaml`, y la imagen sigue arrancando en CPU sin GPU.

### Registro opcional

- Nueva variable `RAFAGA_IMAGE_REGISTRY`, vacía por defecto. Vacía significa lo de siempre:
  `docker compose up --build` construye localmente.
- Con valor (por ejemplo `ghcr.io/<org>`), `compose.yaml` usa
  `image: ${RAFAGA_IMAGE_REGISTRY}/rafaga-<svc>:${RAFAGA_VERSION}` y los scripts de inicio
  hacen `docker compose pull`. Si la descarga falla, avisan y construyen localmente.
- La etiqueta es siempre una versión fija (`RAFAGA_VERSION`, por defecto `1.0.0` en compose, `.env.example` y los scripts), nunca `latest`.
- El registro no recibe credenciales desde el repositorio: si es privado, el usuario hace
  `docker login` por su cuenta. No se publica ninguna imagen desde los scripts de usuario.

## Alternativas rechazadas

- **Imagen base `nvidia/cuda:*-runtime`.** Unos 3 GB solo de base y acopla la versión de
  CUDA a la imagen; ADR-17 ya la descartó.
- **Mantener `[ctk]`.** Simplicidad a cambio de unos 2,5 GB que el solver no usa.
- **Dos imágenes (CPU y GPU).** Complica compose y los scripts; con la reducción, la imagen
  única cabe en el objetivo.
- **Registro obligatorio.** Rompe el uso sin conexión y el principio de construir localmente
  de ADR-25.

## Consecuencias

Positivas:

- Primer arranque más rápido y menos disco.
- Equipos lentos pueden descargar la imagen ya construida.

Negativas y riesgos:

- Si una versión futura de CuPy pide otra biblioteca del toolkit, el solver fallará al
  usarla. La prueba de dispositivo en la imagen lo detecta antes de publicar.
- Las versiones de las ruedas `nvidia-*` deben coincidir con la de CuPy; se fijan juntas.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** Dockerfile y `requirements.txt` reducidos; prueba de tamaño y prueba de
  dispositivo dentro de la imagen.
- **WP-OPS:** `RAFAGA_IMAGE_REGISTRY` y `RAFAGA_VERSION` en `compose.yaml`, `.env.example`,
  `start.sh` y `start.ps1` (pull con caída a build); README en español.
