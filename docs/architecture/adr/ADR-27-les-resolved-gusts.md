# ADR-27 — Turbulencia 3D: LES con entrada sintética para recuperar las ráfagas resueltas (BL-01, BL-02)

Estado: Aceptada
Fecha: 2026-11-13
Sustituye en parte a: la desviación "Equilibrium ABL" de `services/solver/README.md` (longitud de mezcla estacionaria en `section2d` y `volume3d`)
Enmienda: ADR-12 (entrada en 3D), ADR-10 y BR-16 (altura del dominio 3D)

## Contexto

C-3 y FR-37 piden 3D con LBM D3Q19 y LES Smagorinsky. Durante la Fase 3 el solver se desvió
de ADR-12: con una LES gruesa (H/dx ≈ 9) el perfil logarítmico se degradaba a lo largo del
dominio (K a z_a caía de 0,48 a 0,40 en dominio vacío). La corrección fue una longitud de
mezcla de Prandtl `l_m = κ·min(z + z0, d_wall)` en todo el dominio, al estilo de Richards y
Hoxey. Mantiene el perfil medio (K = 1,00–1,05 en dominio vacío), pero la viscosidad
turbulenta resultante es tan alta que el 3D se vuelve, en la práctica, estacionario
(tipo URANS):

- `ti` resuelta queda cerca de 0, y el factor de ráfaga de Lawson cae a su suelo G = 1.
- El 3D pierde lo que lo justificaba frente al 2D: ráfagas resueltas en esquinas y canales.

Requisitos afectados: FR-37 (LES), FR-44/ADR-15 (Lawson con σ_u/Ū de la LES en 3D), NFR-02
(25 M nodos en ≤ 7,2 GB de una GPU de 8 GB) y BR-16 (techo a 6H).

## Decisión

### Modelo de subrejilla

- Smagorinsky local de Hou et al. (ADR-14) con C_s = 0,17 **como única viscosidad
  turbulenta en el interior del flujo**: la escala es `l = min(C_s·dx, κ·d)`, donde `d` es la
  distancia a la pared más cercana (suelo o fachada). Es una amortiguación cerca de la pared,
  no una longitud de mezcla que crece con la altura.
- Se elimina la longitud de mezcla `κ·(z + z0)` de `volume3d`. En `section2d` (2D sin
  estiramiento de vórtices) y `plan2d` se mantiene la longitud actual: allí no hay ráfagas
  resueltas que conservar y el GEM usa la I por defecto del usuario (0,25).
- Se mantienen la ley de pared logarítmica en la primera capa (suelo especular con arrastre
  ajustado, sin doble conteo) y la fuerza de cortadura u*² en la capa superior, que sostienen
  el perfil medio sin depender de la viscosidad turbulenta.

### Turbulencia de entrada

- Generador sintético de Xie y Castro (2008): filtro digital hacia adelante paso a paso.
  Ruido gaussiano sembrado (NumPy, copiado al dispositivo, como en ADR-03) filtrado en el
  plano de entrada con escalas integrales `L_y = L_z ≈ H` y correlación temporal exponencial
  `exp(−π·dt/(2·T))` con `T = L_x / U(z)`, `L_x ≈ 2H`.
- Amplitud por altura con el objetivo `I_u(z) = 1 / ln((z + z0)/z0)`, recortado a
  [0,15; 0,30], con `I_v = 0,75·I_u` e `I_w = 0,5·I_u`.
- La perturbación del 2 % de ADR-12 deja de usarse en `volume3d`.
- Memoria: solo dos planos de entrada (el filtrado y el ruido): unos 2·3·ny·nz·4 B, que es
  despreciable frente a 224 B/nodo.

### Estadísticas para Lawson

- El solver acumula Σu, Σu² (ya incluidos en los 224 B/nodo de ADR-10) durante el promedio
  de ADR-11 y escribe `ti = σ_u/Ū` resuelta a z_a.
- El agregado de Lawson (ADR-15) usa esa `ti` en `volume3d`. El suelo G = 1 solo se aplica a
  celdas sin estadística válida, y el manifiesto lo informa.

### Altura del dominio 3D (BL-02)

- En `volume3d` el techo pasa de 6H a **5H** (H = altura máxima). Se mantiene la condición de
  bloqueo < 3 % de BR-16; si no se cumple con 5H, el techo sube hasta cumplirla.
- Motivo: la LES necesita más tiempo de promedio y conviene ahorrar ≈ 17 % de nodos para que
  los casos habituales quepan en el presupuesto de 8 GB de ADR-10 (≤ 7,2 GB) sin forzar
  coarsening. Con techo de deslizamiento libre y fuerza de cortadura superior, 5H es
  suficiente para el perfil medio (se verifica en la prueba de dominio vacío).
- `plan2d` y `section2d` conservan 6H. Es una enmienda explícita a BR-16 para el 3D; se
  registra en el plan como decisión del arquitecto.

### Enmienda: cierre híbrido RANS/LES aceptado (BL-01, decisión del usuario)

Con Smagorinsky puro y C_s = 0,17 el perfil medio se degradaba a lo largo del fetch (K a z_a
derivaba 10-15 % a la baja). La implementación cerró el problema con un modelo **híbrido**, y
el usuario lo acepta como **desviación aceptada** del texto de arriba:

- **Subrejilla:** las primeras `RANS_LAYERS` = 6 celdas sobre suelo y fachadas usan
  `0,8·κ·min(z + z0, d_wall)` (el esfuerzo resuelto se suma al modelado, por eso la longitud
  RANS se amortigua con 0,8); por encima rige `C_s·dx` de Smagorinsky. La longitud
  `κ(z + z0)` ya no actúa en todo el dominio, sino solo en esa capa de pared.
- **Empuje de campo lejano:** un controlador PI aplica una fuerza de volumen por línea (z, x)
  hacia el perfil logarítmico objetivo, midiendo en las franjas laterales (10 % de cada lado,
  lejos de los edificios). Las estelas conservan su dinámica.
- **Se mantiene** el filtro digital de entrada y la `ti` resuelta; esta sigue alimentando a
  Lawson (ver abajo). `services/solver/README.md` documenta el detalle.
- **Riesgo aceptado:** la capa RANS reduce la `ti` cerca del suelo; se comunica como cribado
  (C-9). La condición de que "no hay longitud de mezcla κ(z+z0)" de BL-01 se sustituye por la
  prueba del campo `hybrid_length_field` y la prueba de dominio vacío.
- **Suelo G = 1:** el manifiesto del agregado incluye `gust_factor` con
  `floor_applies_to = "cells_without_valid_ti"`, las celdas con `ti` resuelta y con la `ti`
  por defecto. Con `ti` resuelta, el GEM supera a la media (G > 1) donde `ti > (1,85 − 1)/3`,
  umbral de la fórmula `G = max(1, (1 + 3 I)/1,85)`.

## Alternativas rechazadas

- **Mantener la longitud de mezcla estacionaria.** Perfil medio correcto, pero sin ráfagas
  resueltas: el 3D no aporta nada a Lawson y FR-37 se cumple solo de nombre.
- **Dominio precursor periódico.** Turbulencia de equilibrio real, pero duplica memoria y
  tiempo; no cabe en 8 GB con 25 M nodos.
- **Agujas de Irwin y rugosidad aguas arriba resueltas.** Requieren varias H de recorrido
  adicional y dx fino; inasumible con dx de 1–2 m.
- **Método de remolinos sintéticos (SEM) o Fourier aleatorio (RFG).** Calidad parecida, pero
  más caros por paso y con más parámetros. El filtro de Xie y Castro es el estándar barato
  en LES urbana.
- **Modelos de subrejilla WALE o Vreman.** Mejor comportamiento cerca de la pared, pero el
  problema no era Smagorinsky, sino la longitud de mezcla añadida encima. Se puede revisar si
  la validación AIJ (SOL-16) lo exige.
- **URANS k-ε acoplado al LBM.** No es nativo de LBM, añade dos campos de transporte y sigue
  sin dar ráfagas resueltas.

## Consecuencias

Positivas:

- `ti` resuelta y el GEM de Lawson vuelven a tener sentido en 3D.
- El 3D vuelve a ser LES, que es lo que pide C-3.

Negativas y riesgos:

- Más tiempo de promedio: con flujo no estacionario, el criterio de ADR-11 tardará más en
  converger y se alcanzará el tope de 6 FT con más frecuencia. Se acepta `converged=false`
  con aviso.
- Con H/dx ≈ 9 la LES está mal resuelta cerca de la pared. Se comunica como cribado (C-9).
- Riesgo de que el perfil medio se degrade de nuevo. Lo controla la prueba de dominio vacío.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER** (BL-01, BL-02 en el solver): prueba de dominio vacío en GPU corta que mide
  I_u en campo lejano a z_a entre 0,15 y 0,30 y K medio entre 0,9 y 1,1; prueba de que el
  agregado de Lawson usa la `ti` resuelta; actualizar `services/solver/README.md` para
  marcar la desviación "Equilibrium ABL" como sustituida en `volume3d`.
- **WP-API** (BL-02): `grid_service` usa 5H de techo en `volume3d` con la comprobación de
  bloqueo; prueba de que el estimador de un caso de referencia cabe en 7,2 GB.
