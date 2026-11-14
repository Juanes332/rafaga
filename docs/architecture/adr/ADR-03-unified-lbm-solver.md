# ADR-03 — Solver LBM único (D2Q9 / D3Q19) con LES y abstracción de dispositivo

Estado: Aceptada
Fecha: 2026-11-13

> Enmienda (2026-11-13, ADR-27): la desviación posterior de C-3 que añadía una longitud de mezcla estacionaria de Prandtl en 3D ("Equilibrium ABL" en `services/solver/README.md`) queda **sustituida**. `volume3d` vuelve a ser LES Smagorinsky, con amortiguación cerca de la pared y turbulencia de entrada sintética.

## Contexto

Hay que simular en tres modos:

- Planta 2D a la altura de análisis (FR-35).
- Cortes verticales (FR-36).
- 3D con LES Smagorinsky (FR-37).

Requisitos que condicionan la elección:

- Se usa CUDA/CuPy si hay GPU NVIDIA y NumPy si no (FR-38, BR-17).
- La diferencia entre CPU y GPU debe ser ≤2 % en K medio (FR-41, US-18).
- Rendimiento: NFR-01 (2D ≤2 min en GPU y ≤10 min en CPU) y NFR-02 (25 M nodos en 3D, ≥100 MLUPS, ≤60 min).
- Restricciones C-2, C-3 y C-4.

## Decisión

Un solo código Lattice-Boltzmann en `services/solver/app/services/`, con estas piezas:

- **Retículas.**
  - D2Q9 para `plan2d` (plano x-y a la altura z_a) y para `section2d` (plano s-z).
  - D3Q19 para `volume3d`.
- **Colisión.** BGK regularizado con viscosidad turbulenta Smagorinsky (forma local de Hou et al., a partir de Π^neq). C_s = 0,17. Los detalles de unidades y los límites de τ están en ADR-14.
- **Abstracción de dispositivo.** `app/services/device/array_module.py` expone `get_xp(device)`, que devuelve `cupy` o `numpy`. Toda la lógica fuera de los núcleos calientes se escribe contra `xp`: contornos, máscaras, promediado y post-proceso.
- **Núcleos calientes en GPU.** Colisión, streaming y forzamiento poroso van fusionados en `cupy.RawKernel` (fuentes `.cu` junto al módulo). Un kernel por paso, con patrón *pull* y dos buffers.
  - Ancho de banda de la RTX 4060: ~272 GB/s.
  - D3Q19 mueve unos 160 B por nodo y paso.
  - Techo teórico: ~1.500 MLUPS. Objetivo sostenido: ≥400 MLUPS.
- **Núcleos calientes en CPU.** NumPy vectorizado e in-place, con el dominio partido en losas (*slabs*) a lo largo de x y procesadas por un `ThreadPoolExecutor`. Los ufuncs de NumPy liberan el GIL, así que se aprovechan los 16 núcleos.
  - Objetivo 2D: ≥20 MLUPS.
  - Objetivo 3D: ≥10 MLUPS.
- **Determinismo.** Las perturbaciones aleatorias se generan siempre en CPU con semilla y se transfieren al dispositivo. Así la prueba de equivalencia CPU/GPU es reproducible.
- **Precisión.** float32 en ambos dispositivos.

## Alternativas rechazadas

- **OpenFOAM** (`simpleFoam` / `pimpleFoam`). Solo CPU, imagen de varios GB, y el usuario lo sustituyó por LBM.
- **Navier-Stokes de volúmenes finitos propio.** El solver de presión (Poisson) es difícil de paralelizar bien en GPU, y la geometría arbitraria exige mallado.
- **Numba-CUDA, Taichi o NVIDIA Warp.** Son toolchains adicionales y la historia del respaldo en CPU es distinta para cada uno. CuPy RawKernel + NumPy mantiene el mismo algoritmo en los dos dispositivos.
- **Cadenas de ufuncs CuPy sin fusionar.** Decenas de lanzamientos de kernel por paso y tráfico de memoria redundante. Las mediciones típicas dan menos de 100 MLUPS en 3D, lo que incumple NFR-02.
- **Colisión MRT.** Más memoria y más operaciones. BGK regularizado con LES es suficientemente estable para este rango (ADR-14).

## Consecuencias

Positivas:

- Un solo modelo numérico para los tres modos.
- La máscara voxel admite cualquier geometría.
- La paridad CPU/GPU se verifica con una prueba.

Negativas y riesgos:

- Los kernels CUDA a mano exigen pruebas de equivalencia contra la ruta NumPy (SOL-17).
- El 3D en CPU es lento: hay límites en ADR-16.
- Si no se alcanzan los 400 MLUPS, NFR-02 se renegocia según A-8.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:**
  - Implementa `array_module`, los kernels `.cu` y su equivalente NumPy.
  - Implementa las pruebas de validación SOL-15 y SOL-16, la de equivalencia SOL-17 y el benchmark SOL-18.
