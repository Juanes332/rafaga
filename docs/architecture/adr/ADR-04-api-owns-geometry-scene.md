# ADR-04 — La api es dueña de la geometría y emite la escena canónica

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

FR-34 exige un único modelo geométrico de fachadas que alimente tanto la discretización 2D como la 3D. El editor necesita validación inmediata (FR-26), vista 3D (FR-27) y recorte de parámetros (US-08), mientras el `solver` puede estar ocupado una hora con un caso 3D. Además, la comparabilidad (BR-11, ADR-23) exige que todas las alternativas compartan malla de salida. Tres paquetes de trabajo deben construir en paralelo sin hablar entre sí.

## Decisión

La `api` es la única dueña de:

- Importación (DXF, STL, OBJ, IFC; ADR-24).
- Modelo paramétrico (edificios con huella, agujeros, altura y escalones).
- Generación de fachadas: las cinco estrategias se expanden en primitivas. La celosía es un prisma poroso paralelo a la arista; las aletas, prismas sólidos perpendiculares; la marquesina, una losa sólida; el retroceso, escalones apilados; la vegetación, un prisma poroso con LAD.
- Validación de geometría (BR-14).
- Especificación de malla:
  - Malla de simulación rotada por dirección, con márgenes BR-16 (5H aguas arriba, 15H aguas abajo, 5H laterales, 6H en altura, bloqueo < 3 % en 3D).
  - Malla de salida norte-arriba común a todo el proyecto.

El resultado es la **escena canónica** (`contracts/scene.schema.json`):

- Coordenadas ENU locales en metros.
- Sin latitud ni longitud.
- Listas de `solids` y de `porous` (modelos `screen` y `canopy_vegetation`), cada una con `source` apuntando al edificio o al elemento de fachada.

Cada trabajo lleva una instantánea inmutable de la escena y de la malla en su `payload`.

El `solver` solo rasteriza y voxeliza esa escena sobre la malla dada. Usa supermuestreo 4× y convierte las primitivas sólidas más finas que media celda en celdas porosas (ADR-13).

## Alternativas rechazadas

- **Paquete Python compartido copiado en ambas imágenes.** Acopla los dos paquetes de trabajo paralelos, sus versiones y sus pruebas. Cada cambio de geometría obligaría a reconstruir y coordinar dos servicios.
- **Geometría en el solver.** La `api` necesitaría un viaje al `solver` (o a la cola) para validar un dibujo o devolver la escena. Si el `solver` está ocupado con un 3D, el editor quedaría bloqueado.
- **Generar la geometría de fachadas en el navegador.** Habría lógica de dominio duplicada y sin pruebas en Python, y la instantánea del trabajo no sería verificable en el servidor.

## Consecuencias

Positivas:

- Un solo dueño, sin código geométrico duplicado.
- El 2D y el 3D se alimentan del mismo modelo (FR-34).
- La escena es reproducible: queda guardada en el `payload`.

Negativas y riesgos:

- La `api` depende de shapely, ezdxf, trimesh, numpy y, en R2, de ifcopenshell. Su imagen crece de forma moderada.
- El esquema de escena es un contrato versionado (`schema_version: "1.0"`). Cambiarlo obliga a coordinar `api` y `solver`.

Qué debe hacer cada paquete de trabajo:

- **WP-API:** compila la escena y comprueba en sus pruebas que valida contra `scene.schema.json`. Calcula `grid.sim` y `grid.output`.
- **WP-SOLVER:** usa como fixtures los ejemplos de `contracts/examples/`, sin reimplementar márgenes ni reglas geométricas.
- **WP-WEB:** usa `GET /alternatives/{id}/scene` para la vista 3D.
