# Constitución — onepiece-estadisticas
Principios innegociables. Toda spec, plan y tarea debe cumplirlos.

1. **Stack simple, sin sobre-ingeniería** — FastAPI + Motor + Pydantic sobre Python. Sin lint, typecheck ni formateador; si no está en `requirements.txt`, no se usa. Nada de capas ni abstracciones que no aporten.
2. **Relación spec-código** — Todo cambio nace en `specs/NNN-nombre/spec.md` (spec → plan → tareas → código, con aprobación por fase). El código y la documentación reflejan la spec; si falta una decisión, se para y se pregunta. `AGENTS.md`/`MEMORY.md` son contexto, no la spec.
3. **Separación de responsabilidades en `main.py`** — Modelos Pydantic, helpers de agregación y endpoints en bloques separados con nombres claros: los endpoints orquestan, la agregación vive en helpers, los modelos solo describen la respuesta; acceso a datos siempre por `db`.
4. **Tests y verificación** — `pytest` + `pytest-asyncio` + `httpx` contra Mongo real, **solo** `onepiece_test` (`conftest.py` aborta la suite si no es exactamente esa base). El agente **no** ejecuta pytest ni uvicorn: los corre el usuario desde PowerShell con `venv\Scripts\python.exe -m pytest -v` y `MONGODB_URI` apuntando a `onepiece` (los tests solo la abren y escriben en `onepiece_test`). Chrome DevTools se usa en solo lectura.
5. **Datos protegidos** — Microservicio de **solo lectura**: no crea, modifica ni borra datos. Nunca `drop`/`delete` sobre la base real `onepiece`; los cambios de esquema o datos se proponen y confirman antes.
6. **Idioma único: español** — Textos, comentarios, logs, documentación, specs, mensajes y commits en español.
