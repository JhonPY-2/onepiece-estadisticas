# MEMORY.md — onepiece-estadisticas

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Microservicio FastAPI + Motor con `/estadisticas/personajes`, `/estadisticas/atletas`, `/estadisticas/tripulaciones` y `/estadisticas/resumen`, con tests aislados en `onepiece_test`.
- Automatización SDD instalada (igual que onepiece-app/frontend): skill `.agents/skills/sdd/`, comandos `/sdd-*` en `.opencode/commands/`, `docs/constitution.md` (6 principios, refundido con tests/verificación e idioma) y reglas en `AGENTS.md`. Primera spec `specs/001-resumen-recompensas/` (aprobada; T1-T3 completadas).
- Spec `002-personajes-sin-tripulacion` **implementada** (T1-T4): `GET /estadisticas/personajes/sin-tripulacion` devuelve `{"cantidad": int}` contando solo `personajes` con `tripulacion` `null` o ausente (cualquier otro valor cuenta como **con** tripulación). Pytest completo **50 passed** (11 nuevos en `tests/test_personajes_sin_tripulacion.py`). Commits 5446d8e, 8926b2a, 43f8296, 2660e7a y 427a09f.
- Spec `003-tripulaciones-cantidad` (Estado aprobada, T1-T4 hechas; falta la validación con `reviewer`): `GET /estadisticas/tripulaciones/cantidad` devuelve `{"cantidad": int}` con el número de documentos de la colección de tripulaciones resuelta con `coleccion_tripulaciones()`, igual que `/estadisticas/tripulaciones`. Pytest completo **62 passed** (12 nuevos en `tests/test_tripulaciones_cantidad.py`). Commits 7db1d6e, 5c16641, 0dddb9b y c3d34ac.

## Decisiones (y por qué)

- En WSL se usa el entorno `.venv-wsl` (en lugar de la carpeta `venv`, que es la de Windows) para evitar mezclar entornos entre sistemas. Si `python3-venv` no está instalado, crear con `python3 -m venv --without-pip .venv-wsl` e instalar con `python3 -m pip --python .venv-wsl/bin/python install -r requirements.txt` (el flag va **antes** del subcomando).
- Instalar en `.venv-wsl` tarda (>10 min) porque el repo está en `/mnt/c` (drvfs). Para verificaciones rápidas se puede crear el venv en el disco ext4 de WSL (p. ej. `/tmp/...`) y lanzar `pytest -v` desde la raíz del repo; el resultado es idéntico.
- SDD con pytest desde PowerShell: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v`. La `MONGODB_URI` apunta a `onepiece` (los tests solo la abren; con `/onepiece_test` el seguro `db.name != main.db.name` falla), y los tests escriben únicamente en `onepiece_test` (lo garantiza `tests/conftest.py`). El agente no ejecuta pytest ni uvicorn; Chrome DevTools solo lectura contra `http://localhost:8000`.
- Los miembros de una tripulación son documentos de `personajes` **y** de `tripulantes`, igual que en `tripulacionController.js` del backend principal.
- La lista de tripulaciones parte de la colección de tripulaciones, no de los miembros: así salen también las que tienen 0 miembros.
- El nombre de la colección de tripulaciones se resuelve en runtime: la colección se llama `tripulacions` por la pluralización por defecto de Mongoose, y `coleccion_tripulaciones()` prueba `tripulaciones` primero por si se cambia el nombre.
- Agentes SDD en `.opencode/agents/`: `coordinator` (primario), `planner` (solo escribe en `specs/`), `implementer` (sin shell, dos fases), `reviewer` (solo lectura). Probados de punta a punta con la spec 002.

## Aprendizajes y errores a evitar

- Los tests nunca deben tocar la base de desarrollo `onepiece` (verifican `db.name != main.db.name`).
- `personajes.tripulacion` es un `ObjectId`, no un texto: un `$group` devuelve ids, hace falta `$lookup` a la colección de tripulaciones para exponer el nombre. Los `PERSONAJES` de los tests con el texto "Sombrero de Paja" son solo para `/personajes` y `/resumen`.
- `tripulaciones.numeroMiembros` está desactualizado (15 y 11 guardados frente a 10 y 10 personajes reales) y no se recalcula en ningún sitio: no usarlo como fuente de verdad.
- En los 20 personajes de `onepiece`, `tripulacion` está guardado como `ObjectId` (verificado en la base, no solo en el esquema).
- La colección se llama `tripulacions` por la pluralización por defecto de Mongoose (verificado con mongoose 9.9.5: `Tripulacion.collection.name === "tripulacions"`); no es un error de nombre.
- `$first` (usado en el `$project` del `$lookup`) requiere MongoDB 4.4+.
- El `implementer` una vez dijo haber creado un archivo que no existía en disco: exigirle siempre la salida literal de la herramienta de escritura y comprobar el archivo en disco (líneas/`ls`).
- `uvicorn` se lanza **sin `--reload`**: tras tocar `main.py` hay que reiniciarlo con `venv\Scripts\python.exe -m uvicorn main:app --port 8000` para ver los endpoints nuevos.
- En tareas sin código nuevo (como T3) el verde llega a la primera y es lo correcto; no forzar un rojo artificial.
- El subagente `reviewer` una vez alucinó RFs ajenos a la spec: validar siempre contra el `spec.md` real.
- Permisos de agentes de opencode: en el encabezado de .opencode/agents/*.md se usa la clave `permission:` en singular y como mapa (`edit: deny`, `bash: { "*": deny, "git diff*": allow }`, `task: { "*": deny, "planner": allow }`, y en `edit` primero `"*"` y después las rutas, porque gana la última regla que coincide). La lista `permissions:` con action/resource/effect que usábamos antes no se aplicaba. Comprobado el 2026-10-18 con archivos de prueba: el reviewer no pudo editar ni ejecutar comandos, y el coordinator no tiene la herramienta edit.
- Cómo comprobar un permiso: pedirle al agente que modifique un archivo de prueba y mirar el disco con Get-Content (no fiarse de lo que cuente el agente), con un archivo de control que sí esté permitido. Los agentes se releen al reiniciar la pestaña de opencode.

## Próximos pasos

- Spec `001-resumen-recompensas` **implementada y validada**, incluido el RF-10 (`personajes_sin_recompensa`); suite de 39 tests en verde en su momento.
- Replicar los 4 agentes (coordinator, planner, implementer, reviewer) a onepiece-app (Jest + Supertest, base `onepiece_agente_scratch`) y a onepiece-frontend (Vitest + Testing Library, Chrome DevTools en solo lectura).
- Opcional del día 3: lanzar varios `@reviewer` en paralelo con focos distintos.
- El MCP chrome-devtools de la pestaña de estadísticas sale con timeout de 30 s (calentar la caché de `npx`).