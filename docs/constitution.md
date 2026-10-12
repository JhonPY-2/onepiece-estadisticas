# Constitución — onepiece-estadisticas

Principios innegociables. Toda spec, plan y tarea debe cumplirlos.

1. **Stack simple y sin tooling obligatorio** — FastAPI + Motor (MongoDB asíncrono) + Pydantic sobre Python. **No** hay lint, typecheck, formateador ni config extra en el repo; si no está en `requirements.txt`, no se usa.

2. **La spec manda** — Todo cambio nace en `specs/NNN-nombre/spec.md` y sigue plan → tareas → código con aprobación explícita entre fases. Nada se implementa si no está en la spec; si falta una decisión, **se para y se pregunta**. `AGENTS.md` y `MEMORY.md` son contexto, no la spec.

3. **Separación de responsabilidades en `main.py`** — Los modelos de respuesta Pydantic, los helpers de agregación y los endpoints van en bloques separados y con nombres claros. Los endpoints orquestan (consultan y devuelven); la lógica de agregación vive en helpers; los modelos solo describen la respuesta. Acceso a datos siempre a través del objeto `db`.

4. **Tests sólo contra `onepiece_test`** — **Nunca** contra la base real `onepiece`. `tests/conftest.py` aborta la suite si la base de los tests no es **exactamente** `onepiece_test`. Los tests de integración usan Mongo real; el fixture aísla y borra sólo `onepiece_test`.

5. **Datos protegidos** — Los endpoints de este microservicio son de **solo lectura**: no crean, modifican ni borran datos. Nunca `drop` ni `delete` sobre datos reales; los cambios de esquema o de datos se proponen y se confirman antes.

6. **Idioma único: español** — Comentarios, mensajes, logs, documentación, specs y commits en español.
