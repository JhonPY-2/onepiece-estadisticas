---
description: "Implementar UNA tarea: /sdd-implement 002-nombre T3"
agent: build
---

Use the skill: sdd

Implementa **SOLO** la tarea $2 de `specs/$1/tasks.md`.

Reglas estrictas (skill sdd):
1. **Una sola tarea cada vez**.
2. **Tests primero** (TDD). Deja claro que **fallan** (antes de escribir código). **NO los ejecutes tú**.
3. **Escribe código** hasta que los tests cubran lo que pide la tarea.
4. **NO ejecutes `pytest`**. Yo lo corro desde **PowerShell**. **Dame el comando exacto**, p. ej. `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` o `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_estadisticas.py -k "nombre" -v`. La `MONGODB_URI` apunta a `onepiece` (los tests solo la abren); los tests escriben únicamente en `onepiece_test`.
5. **NO arranques `uvicorn` (puerto 8000)**: yo lo tengo levantado en otra pestaña. Si `http://localhost:8000` no responde, **PARA y avisa**.
6. **Verificación del contrato HTTP con Chrome DevTools** (si la tarea tiene requisitos de API): abre `http://localhost:8000/docs` o la URL del endpoint, comprueba método, código de estado y JSON. **Ve contándome qué compruebas** para que yo lo vea en el navegador. **Solo acciones de LECTURA** (GET): **NUNCA** crear, editar ni borrar datos. Si hace falta probar escrituras, pídeme primero que levante el servidor contra la base de pruebas y **espera mi confirmación**.
7. **Marca la tarea como completada** (`[x]`) en `specs/$1/tasks.md` **ÚNICAMENTE cuando yo confirme** que los tests pasan y la verificación es correcta.
8. **Sin commit**.
9. **PÁRATE** al terminar. No empieces otra tarea.

$ARGUMENTS
