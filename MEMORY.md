# MEMORY.md — onepiece-estadisticas

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Microservicio FastAPI + Motor con `/estadisticas/personajes`, `/estadisticas/atletas`, `/estadisticas/tripulaciones` y `/estadisticas/resumen`, con tests aislados en `onepiece_test`.
- Automatización SDD instalada (igual que onepiece-app/frontend): skill `.agents/skills/sdd/`, comandos `/sdd-*` en `.opencode/commands/`, `docs/constitution.md` (6 principios, refundido con tests/verificación e idioma) y reglas en `AGENTS.md`. Primera spec `specs/001-resumen-recompensas/` (aprobada; T1-T3 completadas).
- Spec `002-personajes-sin-tripulacion` **implementada** (T1-T4): `GET /estadisticas/personajes/sin-tripulacion` devuelve `{"cantidad": int}` contando solo `personajes` con `tripulacion` `null` o ausente (cualquier otro valor cuenta como **con** tripulación). Pytest completo **50 passed** (11 nuevos en `tests/test_personajes_sin_tripulacion.py`). Commits 5446d8e, 8926b2a, 43f8296, 2660e7a y 427a09f.

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

## Próximos pasos

- Spec `001-resumen-recompensas` **implementada y validada** (T1-T8 completadas). Endpoint `GET /estadisticas/recompensas/resumen` añadido (modelo `RecompensasResumen` con 6 campos `int`, `extra="forbid"`), helpers `normalizar_recompensa`/`promedio_recompensas` en `main.py`. Tests añadidos según tareas (unitarios + integración + regresión). Validación `/sdd-validate` dio veredicto favorable (RF-1–RF-9 cubiertos, regresión incluida, aislamiento a `onepiece_test` garantizado, contrato verificado a mano). Suite completa **36 passed** (`tests/test_recompensas_resumen.py` + `tests/test_estadisticas.py`). `/estadisticas/resumen` intacto.
- `specs/001`: **T9, T10 y T11 hechas**. T9 añadió los tests de RF-10. T10 añadió `personajes_sin_recompensa: int` al modelo `RecompensasResumen` y el contador `if recompensa_norm == 0` en el mismo recorrido del cursor (6º campo en los dos `return`, sin segunda consulta; `main.py` cambió 7 líneas). T11: suite **39 passed**, `/docs` con `GET /estadisticas/recompensas/resumen` junto a `/estadisticas/resumen` y GET real (solo lectura) con seis campos enteros (`personajes_sin_recompensa=0`). Validación RF por RF (RF-1–RF-10) **APROBADA**: todas cumplen con evidencia en `main.py:232-280` + helpers `main.py:73-94` y tests de `tests/test_recompensas_resumen.py`. Suite 39 passed (29 recompensas + 10 estadísticas). Regresión de `/estadisticas/resumen` cubierta por `test_estadisticas_resumen_regresion_sin_campos_nuevos`. Ojo: el subagente reviewer alucinó RFs ajenos a la spec; validar siempre contra `specs/001-resumen-recompensas/spec.md` y los archivos reales.