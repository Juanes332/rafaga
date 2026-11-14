# Ráfaga — Sistema de diseño (contrato WP-WEB)

Contrato visual y de redacción para `services/web` (skills `react-senior` + `frontend-design`).
Prosa en español; nombres de tokens, CSS e identificadores en inglés. Este documento es
la fuente de verdad del entregable WEB-02 (tokens y temas) y la referencia de revisión de
cada pantalla SCR-01..SCR-23.

---

## 1. Dirección

**Tema: un instrumento de medición del viento sobre una mesa de trabajo de laboratorio de
clima urbano.** No es un dashboard SaaS ni un visor CFD de ingeniería. Piensa en un
anemómetro de precisión y en el plano que el arquitecto ya tiene sobre la mesa: superficies
mates y frías, tinta pizarra, rejilla métrica fina, cifras tabulares alineadas como en una
libreta de campo, y el aire —el dato— como lo único que se mueve.

- **Audiencia:** arquitectos y diseñadores sin formación en CFD. Saben leer planos, escalas
  y nortes; no saben qué es un τ de relajación ni deben necesitarlo.
- **Trabajo principal de la interfaz:** ayudar a **decidir entre alternativas de fachada**.
  Todo lo que no acerque a esa decisión (comparar K, ΔK, áreas de zona, clases Lawson) es
  secundario y se queda callado.
- **El elemento memorable (uno solo):** el **campo de flujo animado de partículas sobre la
  planta** en la vista de resultados. Es la primera cosa que el usuario ve al terminar una
  simulación: el viento hecho visible rodeando sus edificios. Todo lo demás —rail,
  inspector, tablas, diálogos— es sobrio, disciplinado y sin decoración.
- **Lo que no somos:** sin degradados decorativos, sin tarjetas idénticas con sombra, sin
  ilustraciones, sin iconografía de "clima" (nubes, soles), sin animaciones de entrada por
  sección.

---

## 2. Color

### 2.1 Principio

Dos familias que nunca se mezclan:

1. **Color de interfaz** (fondo, tinta, reglas, acento de interacción). El acento cobalto
   significa siempre "esto se puede tocar / esto está seleccionado / foco". **Nunca** se usa
   para codificar datos.
2. **Color de datos** (K, ΔK, zonas, Lawson). Proviene de paletas perceptuales cmocean y de
   tres colores de zona derivados de sus extremos. **Nunca** se usa para botones ni estados
   de interfaz.

### 2.2 Tokens — tema claro (por defecto)

```css
:root,
:root[data-theme="light"] {
  /* Surfaces */
  --color-ground: #E8ECEB;          /* "niebla": fondo de la app y del lienzo vacío */
  --color-surface: #F4F6F5;         /* rail, inspector, barra superior */
  --color-surface-raised: #FBFCFC;  /* diálogos, popovers, menús, bottom sheet */

  /* Ink */
  --color-ink: #1E2A30;             /* "pizarra": texto principal, partículas */
  --color-ink-muted: #4C5B62;       /* texto secundario, unidades, ayudas */
  --color-rule: #C5CDCB;            /* reglas divisorias (decorativas, no delimitan controles) */
  --color-control-border: #6E7F86;  /* borde de inputs, sliders, toggles (≥3:1, WCAG 1.4.11) */

  /* Interaction */
  --color-accent: #2B4FD8;          /* cobalto: botón primario, selección, enlaces, foco */
  --color-accent-ink: #FFFFFF;      /* texto sobre --color-accent */
  --color-focus-ring: #2B4FD8;

  /* Data: zones */
  --color-zone-accel: #E0A100;      /* ámbar: SOLO relleno/patrón, nunca texto */
  --color-zone-accel-text: #8A5F00; /* ámbar seguro para texto y etiquetas */
  --color-zone-stagnation: #2F6F73; /* azul petróleo */
  --color-zone-reduction: #6A4C93;  /* violeta */

  /* Status */
  --color-danger: #B3261E;          /* errores, umbrales de seguridad Lawson */
}
```

### 2.3 Tokens — tema oscuro

```css
:root[data-theme="dark"] {
  --color-ground: #172126;
  --color-surface: #1D2A30;
  --color-surface-raised: #24343B;

  --color-ink: #E3E9E8;
  --color-ink-muted: #A3B1B5;
  --color-rule: #33454D;
  --color-control-border: #73878F;

  --color-accent: #7F98FF;
  --color-accent-ink: #172126;
  --color-focus-ring: #7F98FF;

  --color-zone-accel: #F2B934;
  --color-zone-accel-text: #F2B934; /* en oscuro el ámbar ya es legible como texto */
  --color-zone-stagnation: #5FA8AD;
  --color-zone-reduction: #A98BD6;

  --color-danger: #F2867E;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* mismos valores que [data-theme="dark"] */ }
}
```

El fondo oscuro `#172126` es pizarra azulada deliberada (la misma tinta del tema claro,
oscurecida), no un casi-negro neutro. El tema se elige con el toggle de la barra superior;
sin elección explícita sigue `prefers-color-scheme`.

### 2.4 Contraste verificado (WCAG 2.2)

Calculado con la fórmula de luminancia relativa WCAG. Umbral texto normal 4,5:1; componentes
no textuales 3:1.

| Par (claro) | ground | surface | raised |
|---|---|---|---|
| ink `#1E2A30` | 12,34 | 13,54 | 14,30 |
| ink-muted `#4C5B62` | 5,92 | 6,49 | 6,86 |
| accent `#2B4FD8` | 5,49 | 6,02 | 6,36 |
| zone-accel-text `#8A5F00` | 4,74 | 5,20 | 5,50 |
| zone-stagnation `#2F6F73` | 4,84 | 5,31 | 5,61 |
| zone-reduction `#6A4C93` | 5,75 | 6,31 | 6,66 |
| danger `#B3261E` | 5,49 | 6,02 | 6,36 |
| control-border `#6E7F86` (no texto) | 3,50 | — | 4,05 |
| accent-ink `#FFFFFF` sobre accent | 6,54 | | |

| Par (oscuro) | ground | surface | raised |
|---|---|---|---|
| ink `#E3E9E8` | 13,33 | 11,98 | 10,49 |
| ink-muted `#A3B1B5` | 7,42 | 6,67 | 5,84 |
| accent `#7F98FF` | 6,11 | 5,50 | 4,81 |
| zone-accel `#F2B934` | 9,18 | 8,25 | 7,22 |
| zone-stagnation `#5FA8AD` | 6,00 | 5,39 | 4,72 |
| zone-reduction `#A98BD6` | 5,73 | 5,15 | 4,51 |
| danger `#F2867E` | 6,62 | 5,95 | 5,21 |
| control-border `#73878F` (no texto) | 4,36 | — | 3,43 |
| accent-ink `#172126` sobre accent | 6,11 | | |

**Ajustes hechos tras la verificación:**
- El ámbar claro `#E0A100` da 1,90:1 sobre `ground`: queda **prohibido como texto**; toda
  etiqueta de aceleración en tema claro usa `--color-zone-accel-text` `#8A5F00` (4,74:1).
- `--color-rule` (1,36–1,64:1) no alcanza 3:1, así que **no puede delimitar controles**. Se
  añadió `--color-control-border` (claro `#6E7F86`, oscuro `#73878F`, ≥3:1 sobre los fondos
  donde viven los controles) para bordes de inputs, sliders y toggles. `--color-rule` queda
  solo para divisores entre regiones que ya se distinguen por otros medios.
- En oscuro, los pares sobre `raised` más justos (reduction 4,51, stagnation 4,72, accent
  4,81) cumplen; no se usan en texto < 14 px sobre `raised`.

### 2.5 Color de datos

| Capa | Paleta | Dominio | Ticks de leyenda |
|---|---|---|---|
| K = U/U_ref | `cmocean.speed` | fijo 0–2,0 (valores > 2,0 saturan, flecha en leyenda) | 0 · 0,3 · 0,6 · 1,0 · 1,2 · 1,6 · 2,0 |
| ΔK | `cmocean.balance` | simétrico −0,6 a +0,6, 0 en el centro | −0,6 · −0,3 · −0,1 · 0 · +0,1 · +0,3 · +0,6 |
| Lawson (5 clases) | `cmocean.speed` muestreada en 0,1 / 0,3 / 0,5 / 0,7 / 0,9 | categórica | Sentarse · Estar de pie · Pasear · Caminar con prisa · Incómodo |
| Seguridad Lawson | contorno 2 px `--color-danger` + etiqueta | categórica | "Riesgo 15 m/s", "Riesgo 20 m/s" |

- Las leyendas (`KLegend`) siempre son numéricas, con unidad ("K, adimensional"; "m/s") y
  marcas en los umbrales activos (1,2 y 0,3 por defecto, se mueven al cambiar Ajustes).
- Los dominios son **fijos**, no autoescalados: dos alternativas lado a lado deben usar la
  misma escala para que el color signifique lo mismo.
- Las LUT de 256 entradas (WEB-04) se generan de las tablas RGB publicadas por cmocean y
  coinciden con los PNG del solver (±1/255).

### 2.6 Zonas: nunca solo color

Cada zona tiene **relleno + patrón + etiqueta**, de modo que es legible en escala de grises,
con daltonismo y en impresión.

| Zona | Relleno (opacidad 0,45 sobre el campo K) | Patrón SVG | Etiqueta |
|---|---|---|---|
| Aceleración (K > 1,2) | `--color-zone-accel` | rayado diagonal 45°, trazo 1,5 px, paso 6 px | "Aceleración" |
| Estancamiento (K < 0,3) | `--color-zone-stagnation` | puntos 1,5 px, paso 6 px | "Estancamiento" |
| Reducción (ΔK < −0,1) | `--color-zone-reduction` | rayado cruzado ±45°, paso 8 px | "Reducción" |

Las etiquetas se colocan sobre la mancha de mayor área de cada zona (si el área es
> 400 px²) y siempre en la leyenda (`ZoneLegend`) con el área en m² y el porcentaje.

---

## 3. Tipografía

Dos familias claramente distintas, autoalojadas con `@fontsource` (sin CDN: la única salida
a internet permitida es Open-Meteo y OSM, NFR-15).

| Familia | Rol | Pesos |
|---|---|---|
| **Hanken Grotesk** | Toda la interfaz: rail, inspector, botones, tablas, leyendas, cifras | 400, 500, 600 |
| **Literata** | Lectura: notas interpretativas (Lawson, zonas), paneles de ayuda extendida, aviso de limitaciones en informes, cuerpo del PDF | 400, 400 itálica, 600 |

Reglas:
- `font-variant-numeric: tabular-nums;` en **todo** valor numérico (inputs, tablas,
  leyendas, progreso, coordenadas, ETA). Las columnas de cifras se alinean a la derecha.
- Sentence case en todo. **Sin etiquetas en mayúsculas**, sin `letter-spacing` expandido
  sobre etiquetas, **sin eyebrows** encima de los títulos.
- Largo de línea: UI < 80ch; Literata ≤ 72ch con `line-height: 1.6`.
- Los títulos no acentúan una palabra con otro color/peso/itálica.

### Escala tipográfica (razón 1,2 — tercera menor; base 15 px para UI densa)

| Token | Tamaño | rem | Line-height | Uso |
|---|---|---|---|---|
| `--text-xs` | 12 px | 0,75 | 16 px | notas de leyenda, atribución OSM |
| `--text-sm` | 13 px | 0,8125 | 18 px | unidades, ayudas cortas, celdas densas |
| `--text-base` | 15 px | 0,9375 | 22 px | texto de UI por defecto |
| `--text-md` | 18 px | 1,125 | 26 px | títulos de sección del inspector |
| `--text-lg` | 22 px | 1,375 | 28 px | títulos de paso |
| `--text-xl` | 26 px | 1,625 | 32 px | título de proyecto en lista, pantalla de cuenta |
| `--text-2xl` | 32 px | 2 | 38 px | lectura de K bajo el cursor en comparación |
| `--text-reading` | 16 px Literata | 1 | 26 px (1,6) | notas interpretativas |

Pesos: 400 cuerpo, 500 etiquetas y valores, 600 títulos y botón primario. Nunca 700+.

---

## 4. Espacio, forma, elevación, foco y movimiento

**Espaciado** (base 4 px): `--space-1` 4 · `--space-2` 8 · `--space-3` 12 · `--space-4` 16 ·
`--space-6` 24 · `--space-8` 32 · `--space-12` 48. El inspector usa 16 px de margen lateral;
los grupos de parámetros se separan 24 px; los campos dentro de un grupo 12 px.

**Radios (jerarquía, no un radio único):**
- `--radius-control: 4px` — inputs, botones, toggles, chips.
- `--radius-panel: 8px` — diálogos, popovers, bottom sheet, panel flotante de leyenda.
- `--radius-canvas: 0` — lienzo, mapa, campo de flujo, rail e inspector (están anclados al
  borde de la ventana; no flotan).

**Elevación:** solo los elementos que flotan sobre otros llevan sombra (diálogos, popovers,
menús, bottom sheet): `--shadow-float: 0 8px 24px rgb(30 42 48 / 0.18), 0 1px 2px rgb(30 42 48 / 0.12)`
(tintada con la tinta pizarra, no gris genérico). Rail, inspector, tablas y lienzo no tienen
sombra: se separan por cambio de superficie y una regla.

**Bordes como información:** un borde significa "esto es un control" (`--color-control-border`)
o "esto está seleccionado" (2 px `--color-accent`). Los divisores (`--color-rule`) solo separan
regiones. No se encierran bloques de texto en cajas por estética.

**Foco:** `outline: 2px solid var(--color-focus-ring); outline-offset: 2px;` con un halo de
2 px `--color-ground` para que se vea sobre el campo K. Visible siempre con teclado
(`:focus-visible`), nunca eliminado.

**Movimiento:**
- Las partículas son el **único movimiento ambiental** de la app.
- Las transiciones de UI responden a una acción del usuario (abrir, expandir, confirmar),
  duran ≤ 150 ms, `ease-out`, y muestran qué cambió. Sin entradas fade-and-slide por sección,
  sin hover animado en cada fila.
- La barra de progreso de trabajos se actualiza a saltos (cada sondeo), sin animación de
  "shimmer".
- `prefers-reduced-motion: reduce` → partículas desactivadas, se muestran **líneas de
  corriente estáticas** calculadas del mismo campo; transiciones de UI a 0 ms.

---

## 5. Layout

Alineación: todo a la izquierda (texto, títulos, etiquetas). Cifras a la derecha en tablas.
Nada centrado salvo la pantalla de cuenta.

### (a) Espacio de trabajo

Rail izquierdo de pasos (la numeración 1–6 es legítima: es una secuencia real del flujo),
lienzo central, inspector derecho 320–360 px, barra superior delgada (44 px).

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Ráfaga   Proyectos / Edificio de la calle 5        GPU: NVIDIA RTX 4060   ◐  Ana │ 44px
├────────────┬───────────────────────────────────────────────────┬─────────────────┤
│ 1 Proyecto │                                                   │ Celosía         │
│   ✓        │                                                   │                 │
│ 2 Geometría│              LIENZO (planta métrica,              │ Porosidad       │
│   ✓        │              mapa opcional debajo,                │ [====|-----] 40%│
│ 3 Viento   │              rejilla 1 m / 10 m)                  │ Defecto 40 %    │
│   ●        │                                                   │ Rango 5–95 %  ⓘ │
│ 4 Alterna- │                                                   │                 │
│   tivas    │                                                   │ Altura          │
│ 5 Simular  │                                                   │ [ 3,0 ] m       │
│   🔒 Fija  │                                                   │                 │
│   la ubi-  │   ┌──────────┐                                    │ Separación      │
│   cación   │   │ escala   │  N↑                                │ [ 0,5 ] m       │
│ 6 Comparar │   └──────────┘                                    │                 │
│   🔒       │                                                   │ [Aplicar]       │
├────────────┴───────────────────────────────────────────────────┴─────────────────┤
  rail 200px            canvas flex                                 inspector 340px
```

- Estados del paso: completado (✓ en tinta), actual (barra 3 px cobalto a la izquierda +
  peso 600), bloqueado (texto `ink-muted`, candado y motivo en una línea:
  "Fija la ubicación"). Los pasos bloqueados son enfocables y anuncian el motivo.
- El badge de cómputo es texto plano: "GPU: NVIDIA RTX 4060" o "CPU: 16 núcleos". Un punto
  de salud a la izquierda (relleno = servicio sano; contorno = sin conexión) con texto
  alternativo. Sin cadenas "A · B · C".

### (b) Vista de resultados

```
┌──────────────────────────────────────────────────────────────────┬───────────────┐
│ Dirección [E ▾]  Capa (•) K  ( ) Velocidad  ( ) Lawson   [Zonas] │ Resultado     │
│                                                                   │ Base, E       │
│      ~~~~~~~~ partículas ~~~~~~~~                                 │ K medio 0,74  │
│   ~~~~~~╔════╗~~~~~~~~~~~~~                                       │ K máx  1,63   │
│  ~~~~~~~║    ║~~~ ////// ~~~                                      │               │
│  ~~~~~~~╚════╝~~~ ////// aceleración                              │ Zonas    m²  %│
│   ~~~~~~~~~~~ ::::: estancamiento                                 │ Acel.  412 6,1│
│                                                                   │ Estanc.880 13 │
│ ┌ K (adimensional) ───────────────────┐   [❚❚ Pausar]  N↑  ├─50m─┤│               │
│ │▕████████████████████████████▏ ▸     │                           │ [Exportar PNG]│
│ │ 0   0,3  0,6  1,0 1,2  1,6  2,0     │                           │               │
│ └─────────────────────────────────────┘                           │               │
├───────────────────────────────────────────────────────────────────┴───────────────┤
│ Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en       │
│ túnel de viento.                                                                   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

La franja del aviso es permanente en toda vista de resultados, comparación y exportación;
`--color-surface`, texto `--text-sm` en tinta, sin icono de alerta (es información, no error).
Al pasar el cursor sobre el campo, una lectura flotante muestra "K 1,34 — 5,1 m/s".

### (c) Comparación a pantalla completa

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ✕ Salir   A: Base  ⇄  B: Celosía 40 %     Dirección E   [ΔK]   [Zonas]          │
├──────────────────────────────────────┃─────────────────────────────────────────┤
│ A  Base                              ┃                       Celosía 40 %  B   │
│                                      ┃                                         │
│        campo K de A                  ◀▶       campo K de B                       │
│                                      ┃                                         │
│                                      ┃  (tirador vertical: arrastrable,        │
│                                      ┃   ← → 2 %, Mayús+← → 10 %)              │
├──────────────────────────────────────┸─────────────────────────────────────────┤
│ ▴ Áreas por zona y clase de confort                                             │
│              Aceleración     Estancamiento    Reducción    Sentarse  …  Incómodo │
│ Base         412 m² 6,1 %    880 m² 13,0 %    —            …                     │
│ Celosía 40 % 236 m² 3,5 %    1 020 m² 15,1 %  540 m² 8,0 % …                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo …     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

- El tirador es un `role="slider"` con `aria-valuenow` en porcentaje y etiqueta
  "Posición del comparador".
- ΔK reemplaza la vista dividida por un único mapa `balance` con el rayado cruzado de
  reducción; la tabla no cambia.
- Si los resultados no son comparables, el lienzo muestra la lista de diferencias (ver §8).

### (d) Primera ejecución — crear cuenta local

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│               Ráfaga                                        │
│               Crea tu cuenta local                          │
│               Tus proyectos se guardan solo en este equipo. │
│                                                             │
│               Correo      [                         ]       │
│               Contraseña  [                         ]       │
│               Mínimo 10 caracteres.                         │
│                                                             │
│               [ Crear cuenta ]                              │
│                                                             │
│    (fondo: líneas de corriente estáticas muy tenues, 8 %)   │
└─────────────────────────────────────────────────────────────┘
```

Columna de 360 px centrada. Es la única pantalla centrada.

### (e) Lista de proyectos

Una lista/tabla, no una cuadrícula de tarjetas idénticas.

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Proyectos                                             [ Nuevo proyecto ]  │
├───────────────────────────────────────────────────────────────────────────┤
│ Nombre                         Ubicación              Actualizado     ⋯   │
│ Edificio de la calle 5         ##,#####  ##,#####     hace 2 h        ⋯   │
│ Conjunto norte                 Sin ubicación          ayer            ⋯   │
│ Copia de Conjunto norte        Sin ubicación          12 nov 2026     ⋯   │
└───────────────────────────────────────────────────────────────────────────┘
```

(`##,#####` marca el formato de 5 decimales; ningún valor de ubicación aparece como ejemplo, BR-18.) Menú ⋯: Renombrar,
Duplicar, Eliminar (diálogo que nombra el proyecto). Vacío: ver §8.

### (f) Responsivo (hasta 360 px)

| Ancho | Comportamiento |
|---|---|
| ≥ 1280 px | Tres columnas como en (a). |
| 1024–1279 | Inspector 320 px; rail colapsa a números + nombre corto. |
| 768–1023 | Rail se vuelve stepper horizontal bajo la barra superior; inspector se convierte en panel deslizable derecho (botón "Parámetros"). |
| < 768 (hasta 360) | Stepper horizontal desplazable con el paso actual centrado; inspector como **bottom sheet** (altura 40 % / 90 %) con tirador; comparación con tirador horizontal (A arriba, B abajo); tabla de áreas con scroll horizontal en su propio contenedor (nunca la página). |

El editor de geometría en < 768 px permite ver y editar parámetros pero muestra
"Dibujar funciona mejor en una pantalla más grande" sin bloquear.

---

## 6. Inventario de componentes

Primitivas shadcn/ui (`components/ui/`, planas): `Button`, `Input`, `Label`, `Slider`,
`Select`, `RadioGroup`, `Switch`, `Toggle`, `ToggleGroup`, `Tooltip`, `Popover`, `Dialog`,
`AlertDialog`, `Sheet` (bottom sheet / panel lateral), `DropdownMenu`, `Tabs`, `Progress`,
`Table`, `Command` (búsqueda de lugares), `Sonner` (avisos breves). Se re-tematizan con los
tokens de §2–4; ninguna conserva el radio/sombra por defecto de shadcn.

Componentes propios (cada uno con el patrón de cuatro archivos de `react-senior`):

| Componente | Base | Responsabilidad |
|---|---|---|
| `StepRail` | `nav` + lista ordenada | Pasos 1–6, estados completado/actual/bloqueado con motivo; versión stepper horizontal. |
| `Inspector` | `aside` / `Sheet` | Contenedor contextual del objeto seleccionado; título + grupos de `ParamField`. |
| `ParamField` | `Label` + `Input` + `Slider` + `Tooltip` | Valor con unidad, "Defecto X", "Rango a–b", ayuda (definición, rango, defecto) en foco y hover; muestra el mensaje de ajuste cuando la API recorta un valor. |
| `WindRose` | SVG + d3-shape | 16 sectores, frecuencia radial, color por velocidad p50 (cmocean speed); modo selector de direcciones (clic/teclado) con cobertura %. |
| `KLegend` | SVG | Barra de color con ticks numéricos, unidad, marcas de umbral, flecha de saturación. |
| `ZoneLegend` | lista | Muestra patrón + color + nombre + área m² + %. |
| `FlowCanvas` | WebGL2 (`engines/particles`) | Campo K + partículas + zonas + lectura bajo cursor. |
| `SwipeCompare` | `role="slider"` | Dos capas recortadas por el tirador; teclado y arrastre. |
| `JobProgress` | `Progress` + texto | Por dirección: fase, %, ETA, dispositivo, Cancelar / Reintentar. |
| `ComputeBadge` | texto + punto de salud | "GPU: <modelo>" / "CPU: N núcleos"; estado de servicios en popover. |
| `Disclaimer` | `p` | Franja fija con el aviso FR-48. |
| `EmptyState` | texto + una acción | Una frase de invitación y un botón primario; sin ilustración. |
| `ErrorNotice` | `role="alert"` | Causa + solución + acción opcional. |
| `MapPicker` | MapLibre | Mapa con atribución OSM, marcador, búsqueda, coordenadas. |
| `GeometryEditor` | SVG | Dibujo, selección de aristas, rejilla, deshacer. |
| `Viewer3D` | react-three-fiber | Geometría / resultados 3D. |

---

## 7. Campo de flujo de partículas (elemento memorable)

- **Técnica:** WebGL2, posiciones de partículas en texturas ping-pong (RGBA32F), campo de
  velocidad (ux, uy del resultado) como textura RG32F con muestreo bilineal en coordenadas
  métricas; trazos dibujados en un framebuffer que se atenúa cada cuadro.
- **Cantidad:** 16 384 partículas por defecto; 32 768 si `devicePixelRatio ≥ 2` y el cuadro
  medio < 10 ms; 8 192 en pantallas < 768 px. Densidad ajustada para ~1 partícula por
  60 px² de lienzo.
- **Velocidad:** desplazamiento por cuadro = `K_local × 0,6 px` a zoom 1 (normalizado a
  K, no a m/s, para que la lectura sea relativa a U_ref); tope 3 px/cuadro.
- **Vida y reaparición:** vida aleatoria 2–6 s; reaparición aleatoria en celdas de fluido
  (nunca dentro de sólidos); 0,3 % por cuadro reaparece aguas arriba para mantener el aporte.
- **Estela:** atenuación por cuadro del 4 % (opacidad × 0,96) → estelas de ~1 s.
- **Color:** `--color-ink` al 70 % sobre el campo K (cmocean speed) al 85 %; en oscuro, la
  tinta clara `#E3E9E8` al 70 %. Las partículas no se colorean por velocidad: el color ya lo
  da el campo; la partícula aporta dirección y ritmo.
- **Interacción:** botón "Pausar"/"Reanudar" (también tecla `Espacio` con el lienzo enfocado);
  lectura bajo el cursor "K 1,34 — 5,1 m/s" en Hanken Grotesk tabular; zoom y desplazamiento
  reinician estelas sin parpadeo.
- **Respaldo:** sin WebGL2 o con `prefers-reduced-motion` → líneas de corriente estáticas
  (integración RK2 desde semillas en rejilla de 24 px, trazo 1 px tinta 60 %).
- **Presupuestos:** ≤ 4 ms de GPU por cuadro en gráfica integrada a 1080p; 60 fps objetivo,
  degradación automática (mitad de partículas) si la media de 30 cuadros > 20 ms; pausa
  automática cuando la pestaña no está visible; memoria de texturas ≤ 32 MB.

---

## 8. Redacción (es-CO)

### Principios
- **Voz:** la del instrumento: precisa, tranquila, en segunda persona (tú), sin humor ni
  disculpas. Nada de "¡Ups!", "Lo sentimos", signos de exclamación ni emojis.
- **Sentence case** en títulos, botones y pestañas.
- **Verbos activos** que dicen exactamente qué pasa: "Guardar cambios", "Simular", "Crear
  alternativa", "Exportar PNG". Nunca "Enviar", "Aceptar" ni "OK" como acción principal.
- **Nombres estables a lo largo del flujo:** botón "Simular" → estado "Simulación en curso"
  → aviso "Simulación lista". "Exportar PNG" → "Exportando PNG" → "PNG listo para descargar".
  "Generar informe" → "Generando informe" → "Informe listo".
- **Nombres del usuario, no del sistema:** "Tamaño de celda", no "dx"; "Dispositivo de
  cálculo", no "backend"; "Rosa de vientos", no "distribución direccional".
- Cada texto hace un solo trabajo. Las ayudas largas van en Literata dentro del panel de
  ayuda, no en tooltips.

### Errores: causa + solución

| Situación | Texto |
|---|---|
| Malla demasiado grande | "La malla no cabe en la memoria de la GPU: necesita 9,1 GB y hay 7,2 GB disponibles. Usa un tamaño de celda de 1,5 m o activa el ajuste automático." |
| ERA5 sin red | "No se pudo descargar el viento histórico porque no hay conexión y este sitio no está en caché. Escribe la dirección y la velocidad de referencia a 10 m, o vuelve a intentarlo con conexión." |
| Importación fallida | "El archivo DXF no tiene polilíneas cerradas. Cierra los contornos de los edificios en tu programa de CAD y vuelve a importarlo." |
| Falta ubicación | "Fija la ubicación del proyecto para obtener el viento del sitio. Haz clic en el mapa, busca un lugar o escribe las coordenadas." |
| Comparación incompatible | "Estos resultados no se pueden comparar porque tienen distinto tamaño de celda (1,0 m y 2,0 m) y distinta dirección (E y NE). Simula ambas alternativas con los mismos parámetros." |
| GPU no detectada | "No se detectó una GPU NVIDIA, así que las simulaciones usarán la CPU y tardarán más. Si tienes una GPU NVIDIA, revisa el controlador y la sección «GPU» del README." |

### Estados vacíos (cadenas exactas)

| Lugar | Texto | Acción |
|---|---|---|
| Lista de proyectos | "Crea tu primer proyecto" | "Nuevo proyecto" |
| Paso Proyecto sin ubicación | "Elige dónde está tu proyecto" | (mapa + búsqueda) |
| Geometría vacía | "Dibuja o carga tu primer edificio" | "Dibujar bloque", "Importar archivo" |
| Fachadas sin edificios | "Dibuja o carga tu primer edificio" | "Ir a Geometría" |
| Alternativas (solo base) | "Crea una alternativa para probar una estrategia de fachada" | "Crear alternativa" |
| Simular sin trabajos | "Elige direcciones y simula tu primera alternativa" | "Simular" |
| Comparar con < 2 resultados | "Simula al menos dos alternativas en la misma dirección para compararlas" | "Ir a Simular" |
| Informes | "Genera un informe cuando tengas resultados" | "Generar informe" (deshabilitado con motivo) |

### Aviso de limitaciones (FR-48, texto exacto)

> Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento.

### Números y unidades
- `Intl.NumberFormat('es-CO')`: coma decimal, punto de miles ("1.020 m²", "0,74").
- Espacio fino (U+2009) entre número y unidad: "5,1 m/s", "40 %", "12 m", "1,2 kg/m³".
- Precisión: K y ΔK con 2 decimales; velocidades 1 decimal; áreas enteras en m²;
  porcentajes 1 decimal; coordenadas 5 decimales; altitud entera en m; densidad 3 decimales.
- Direcciones con nombre de 16 rumbos en español (N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSO,
  SO, OSO, O, ONO, NO, NNO) y grados entre paréntesis en ayudas: "E (90°)".
- Fechas: "12 nov 2026"; tiempos relativos para < 48 h ("hace 2 h").

### Glosario de la interfaz

| Término | Definición mostrada |
|---|---|
| K | Cuánto más (o menos) viento hay a la altura del peatón comparado con el mismo punto sin edificios. K = 1 igual; K = 1,5, un 50 % más. |
| ΔK | Diferencia de K entre una alternativa y el caso base. Negativo: la alternativa reduce el viento. |
| Aceleración | Zonas donde K supera 1,2: el viento es notablemente más fuerte que en campo abierto. |
| Estancamiento | Zonas donde K es menor que 0,3: el aire casi no se mueve. |
| Reducción | Zonas donde la alternativa baja K en más de 0,1 respecto al caso base. |
| Rosa de vientos | De dónde sopla el viento en el sitio, con qué frecuencia y a qué velocidad, según 10 años de datos históricos. |
| Rugosidad | Qué tan accidentado es el terreno alrededor (z0, en metros). Más rugosidad frena el viento cerca del suelo. |
| Confort Lawson | Qué actividades peatonales son cómodas en cada punto según la frecuencia de vientos fuertes. |

---

## 9. Autorrevisión frente a los valores por defecto genéricos

| Rasgo genérico (skill) | Cómo lo evita este sistema |
|---|---|
| 1. Fondo crema cálido + serif display de alto contraste + acento terracota | Fondo niebla fría `#E8ECEB`, tinta pizarra, acento cobalto. La serif (Literata) se reserva para lectura, nunca como display. |
| 2. Fondo casi negro con un único acento ácido | El oscuro es pizarra azulada `#172126` derivada de la tinta; el acento es cobalto suavizado, y el color fuerte está en los datos (cmocean), no en un acento de marca. |
| 3. Layout de periódico: reglas finas, radio cero, columnas densas | Hay radio jerárquico (4/8/0), las reglas son mínimas y solo separan regiones, el layout es de herramienta (rail-lienzo-inspector), no de columnas editoriales. |
| 4. Kit SaaS de tarjetas idénticas con sombra y degradados | Proyectos en lista/tabla; sin tarjetas repetidas; sombra solo en lo que flota, tintada; ningún degradado decorativo (los únicos degradados son escalas de datos). |
| 5. Chrome de plantilla: eyebrows en mayúsculas, meta con puntos medios, "PALABRA — fragmento", casi-negro neutro, monoespaciada para datos, "→" en enlaces | Sin mayúsculas ni eyebrows; el badge es "GPU: NVIDIA RTX 4060" sin puntos medios; las cifras usan Hanken Grotesk tabular, no monoespaciada; los botones no llevan flechas añadidas. |

**Revisiones hechas en esta pasada:**
- La primera idea de la barra superior unía proyecto, dispositivo y usuario con puntos
  medios; se cambió a regiones separadas por espacio y texto con dos puntos.
- La lista de proyectos se había esbozado como cuadrícula de tarjetas con miniatura; se
  cambió a lista con columnas tabulares (es lo que el arquitecto escanea: nombre, ubicación,
  fecha).
- Se había previsto una fuente monoespaciada para coordenadas y lecturas de K; se sustituyó
  por Hanken Grotesk con `tabular-nums`, que alinea igual sin el tono "terminal".
- El ámbar de aceleración no pasaba contraste como texto y las reglas no servían como borde
  de control: se añadieron `--color-zone-accel-text` y `--color-control-border` (§2.4).
- La pantalla de cuenta tenía partículas animadas de fondo; se cambió a líneas de corriente
  estáticas tenues para que el único movimiento siga siendo el de los resultados.
