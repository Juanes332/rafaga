# ADR-28 — Capacidad del dispositivo del solver y aviso antes de un 3D en CPU (BL-06)

Estado: Aceptada
Fecha: 2026-11-13
Complementa: ADR-10, ADR-16, ADR-17, ADR-22

## Contexto

NFR-03 permite el 3D en CPU solo como caso reducido (≤ 3 M nodos en ≤ 90 min) y exige que
se informe una estimación previa. Un usuario sin GPU puede lanzar un 3D que tarda más de una
hora sin enterarse. La SPA necesita saber, antes de lanzar, en qué dispositivo correrá el
trabajo y cuánto tardará, y la información debe venir de un endpoint autenticado: la SPA
nunca habla con el solver (ADR-01).

## Decisión

La capacidad fluye en una sola dirección: **solver → db → api → web**.

1. **Solver.** Al arrancar ejecuta la prueba de dispositivo de ADR-17 y un microbenchmark
   corto (`mlups_2d`, `mlups_3d`) en el dispositivo elegido por `RAFAGA_DEVICE`. Hace upsert
   de su fila en `solver_nodes` (`device`, `gpu_name`, `vram_total_bytes`,
   `ram_budget_bytes`, `cpu_cores`, `mlups_2d`, `mlups_3d`) y la refresca cada 5 s
   (`heartbeat_at`). El solver no expone nada más que `/health`.
2. **db.** `solver_nodes` (job-contract §2.6) es la única fuente de verdad. No hay columnas
   nuevas.
3. **api.** Lee la fila con `heartbeat_at` más reciente. Si tiene más de 30 s, el solver se
   considera fuera de línea.
   - `GET /api/v1/system/status` (bearer obligatorio, API-09) expone
     `solver {online, device, gpu_name, vram_total_bytes, ram_budget_bytes, cpu_cores,
     mlups_2d, mlups_3d, heartbeat_at}`. No se crea otro endpoint.
   - `POST /api/v1/simulations/estimate` (API-46) resuelve el dispositivo efectivo
     (`auto` → el de la fila; `gpu` pedido sin GPU → `cpu`) y calcula
     `eta_seconds = nodos × pasos / (mlups × 1e6)` con `mlups_3d` de la fila. Si
     `mlups_3d` es nulo, usa la constante conservadora de ADR-16 y la ETA se marca como
     aproximada.
4. **web.** `ComputeBadge` muestra el dispositivo con TanStack Query sobre
   `/system/status`. En el paso Simular (SCR-12), si `kind = volume3d` y el dispositivo
   efectivo de la estimación es `cpu`, el botón de lanzar abre un diálogo modal con:
   - la ETA en horas y minutos, el número de nodos y el tope de NFR-03;
   - la recomendación de usar 2D o una GPU;
   - una confirmación explícita (acción primaria "Lanzar en CPU"; el foco inicial y Escape
     van a "Cancelar").
   Sin confirmación no se llama a `POST /simulations`. Con el solver fuera de línea el
   lanzamiento se deshabilita con explicación.

## Alternativas rechazadas

- **La SPA consulta al solver directamente.** Rompe ADR-01: el solver no se publica y no
  tiene autenticación de usuario.
- **Un endpoint nuevo `/system/capabilities`.** Duplica API-09, que ya devuelve lo mismo
  autenticado.
- **Bandera `confirm_cpu_3d` obligatoria en `POST /simulations`.** Obliga a cambiar el
  contrato y castiga a clientes expertos y a las pruebas de humo; el riesgo que se protege
  es de experiencia de usuario, no de seguridad. El límite duro sigue siendo el de ADR-16.
- **Bloquear siempre el 3D en CPU.** NFR-03 lo permite con caso reducido.

## Consecuencias

Positivas:

- El usuario ve el coste antes de pagarlo, como pide NFR-03.
- No cambian tablas ni contratos: solo el uso de datos que ya existen.

Negativas y riesgos:

- La ETA depende de un microbenchmark corto y puede desviarse ±30 %. El diálogo lo dice.
- Si el solver cambia de dispositivo después de la estimación, el trabajo usa el nuevo; el
  campo `device_used` lo refleja.

Qué debe hacer cada paquete de trabajo:

- **WP-SOLVER:** prueba de que la fila de `solver_nodes` incluye `mlups_3d` en CPU y GPU.
- **WP-API:** prueba de que `/system/status` exige bearer (401 sin él) y de que la
  estimación de un `volume3d` con nodo CPU devuelve `device = cpu` y una `eta_seconds`
  calculada con `mlups_3d`.
- **WP-WEB:** prueba (Vitest + MSW) de que un 3D con estimación en CPU muestra el diálogo
  con la ETA, que Cancelar no envía nada y que confirmar envía `POST /simulations`.
