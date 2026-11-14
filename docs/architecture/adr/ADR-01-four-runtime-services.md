# ADR-01 — Cuatro servicios de ejecución: api, solver, web y db

Estado: Aceptada
Fecha: 2026-11-13

## Contexto

Ráfaga combina tres cargas de trabajo muy distintas:

- Peticiones interactivas cortas: CRUD de proyectos, editor de geometría, mapa, clima de viento (FR-04, FR-11..FR-34).
- Cálculo numérico largo y con GPU: LBM 2D y 3D, con trabajos 3D de hasta 60 min (FR-35..FR-41, NFR-01..NFR-03).
- Una SPA estática (FR-52, NFR-04).

Hay restricciones del usuario que se deben respetar:

- Un único servicio `solver` para 2D y 3D (C-2).
- OpenFOAM queda sustituido por LBM D3Q19 (C-3).
- Postgres ≥16 hace también de cola.
- No se usan Redis ni nginx.
- Cada servicio tiene su propia imagen (delivery-contract).

Requisitos relacionados: NFR-13 (un trabajo fallido no afecta a los demás), US-09 y US-10 (la interfaz debe seguir respondiendo mientras se simula), BR-17 (respaldo en CPU).

## Decisión

La forma es `services`, con cuatro componentes de ejecución:

| Servicio | Skill | Responsabilidad |
|---|---|---|
| `api` | fastapi-senior | Autenticación, proyectos, geometría y escena canónica, viento y datos externos, encolado de trabajos, lectura de resultados y cálculo de áreas de zonas |
| `solver` | fastapi-senior (solo `/health`) | Cola de trabajos, LBM D2Q9/D3Q19, post-proceso, Lawson, PNG y PDF |
| `web` | react-senior + frontend-design | SPA servida con `serve -s dist -l tcp://0.0.0.0:3000` |
| `db` | imagen oficial postgres (piso 16) | Datos y cola de trabajos (ADR-02) |

Cómo se reparten las fronteras:

- `api` no importa CuPy ni contiene código de solver.
- `solver` no expone rutas de negocio.
- `web` solo habla con `api`.
- `solver` y `api` se comunican únicamente a través de Postgres (tablas `jobs`, `results` y otras de `contracts/job-contract.md`) y del volumen `rafaga-data` (ADR-18).
- `solver` y `db` no publican puertos al host.

## Alternativas rechazadas

- **Monolito modular con worker en proceso.** Las ruedas CUDA (más de 1 GB) acabarían en la imagen de la API. Un OOM de GPU o un fallo del kernel tumbaría la API y `/health`, y no se podría liberar la memoria GPU de forma fiable.
- **`worker-2d` y `worker-3d` separados.** El usuario los fusionó. Habría dos imágenes con el mismo código LBM, y la equivalencia 2D/3D (FR-34) se mantendría en dos sitios.
- **Worker OpenFOAM.** No usa la GPU, la imagen ocupa varios GB y el usuario lo sustituyó explícitamente por LBM D3Q19 (enmienda 2).
- **Microservicios por dominio (geometría, viento, informes).** Tendrían fronteras sin ninguna presión que las justifique: un solo usuario local, un solo ritmo de despliegue y nada que escalar por separado.

## Consecuencias

Positivas:

- El cómputo pesado está aislado y la API sigue respondiendo durante las ejecuciones 3D.
- La imagen GPU es independiente de las demás.
- Hay tres paquetes de trabajo de desarrollo en paralelo con contratos explícitos (OpenAPI, escena y trabajos).

Negativas y riesgos:

- El contrato de las tablas compartidas entre `api` y `solver` debe mantenerse con disciplina. Lo protege `schema_meta.job_contract_version`.
- Hay que levantar cuatro contenedores. El script `start` lo oculta (ADR-25).

Qué debe hacer cada paquete de trabajo:

- **WP-API:** es dueño de las migraciones de todas las tablas, incluidas las de trabajos.
- **WP-SOLVER:** solo lee y escribe las columnas documentadas.
- **WP-WEB:** nunca llama al `solver`.
- **WP-OPS:** define los cuatro servicios en `compose.yaml` sin publicar `solver` ni `db`.
