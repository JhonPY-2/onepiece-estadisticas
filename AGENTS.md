# AGENTS.md

Repositorio: onepiece-estadisticas (microservicio FastAPI que expone `/estadisticas/*`).

## Información clave

- Tecnologías: FastAPI + Motor (MongoDB asíncrono) + Pydantic. `main.py`, `tests/`, `pytest.ini`.
- Punto de entrada: `main:app` (uvicorn).
- Endpoints: `/` → mensaje; `/estadisticas/personajes`, `/estadisticas/atletas` (agrupado por `$equipo` desc), `/estadisticas/tripulaciones` (miembros por tripulación vía `$lookup`), `/estadisticas/resumen`. `EquipoConteo._id` se expone como `equipo` y `TripulacionConteo._id` como `tripulacion`.
- `personajes.tripulacion` es un `ObjectId` que referencia la colección de tripulaciones, no un texto: por eso `/estadisticas/tripulaciones` usa `$lookup` y no un `$group` simple.
- La colección de tripulaciones se llama `tripulacions` por la pluralización por defecto de Mongoose; `coleccion_tripulaciones()` la resuelve en runtime probando `tripulaciones` primero por si se cambia el nombre.
- Un miembro es un documento de `personajes` **o** de `tripulantes` (mismo criterio que `tripulacionController.js` del backend principal).

## Configuración / Ejecución

- Local (WSL/Ubuntu): `python3 -m venv .venv-wsl && source .venv-wsl/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload --port 8000`. Nota: la carpeta `venv` existente es la de Windows y no se debe tocar desde WSL (usar `.venv-wsl`).
- Windows: `venv\Scripts\activate`.
- Docker: `python:3.12-slim`, instala `requirements.txt`, expone `8000`, ejecuta `uvicorn main:app --host 0.0.0.0 --port 8000`.
- Docs API: http://localhost:8000/docs. Requiere `MONGODB_URI` en `.env`.

## Tests

- `pytest -v` desde la raíz. `pytest.ini`: `pythonpath=.` `testpaths=tests`, `asyncio_mode=auto`, `asyncio_default_fixture_loop_scope=function`.
- Aislamiento: conecta a `MONGODB_URI`, usa DB `onepiece_test`, verifica `db.name != main.db.name`, hace monkeypatch de `main.db`, limpia al terminar. Peticiones vía `httpx.ASGITransport`.
- Casos: sin datos devuelve ceros/`None`. Datos de prueba: Luffy mayor recompensa (3e9), Equipo A aparece 2 veces. Tripulaciones usan `ObjectId` + documentos en `tripulaciones`, como la base real: se comprueba la mezcla `personajes` + `tripulantes`, las tripulaciones sin miembros (0) y las referencias sin documento (se ignoran).
- CI: push/PR a `master`, `mongo:7` en 27017, `MONGODB_URI=mongodb://localhost:27017/onepiece`, Python 3.12 + `pytest`.

## Notas del entorno

- `.env` local con `MONGODB_URI=mongodb://localhost:27017/onepiece`. `.gitignore` excluye `venv/`, `.env`, `__pycache__/`, `.pytest_cache/`.
- Python 3.12 (Docker/CI). Sin herramientas de lint/typecheck/format.
- README enlaza a proyecto principal: https://github.com/JhonPY-2/onepiece-app.

## Memoria

- Al empezar, lee `MEMORY.md` para conocer el estado del proyecto y las decisiones tomadas.
- Al terminar una tarea, actualízalo: estado actual, decisiones importantes (con su porqué) y errores a evitar.
- Mantenlo breve (máximo ~50 líneas): resume o elimina lo que ya no aporte.
- Si algo se convierte en una regla permanente, propón moverlo a `AGENTS.md` en lugar de dejarlo en la memoria.
- No guardes nunca datos sensibles (claves, tokens, datos personales).

## Límites

- No tocar `.env`.
- No crear ni modificar la carpeta `venv` (es del entorno Windows).
- No usar la base `onepiece` de desarrollo (los tests usan solo `onepiece_test`).
- No hacer commit ni push.
- No instalar dependencias sin preguntar.
- Siempre: actualizar `MEMORY.md` al terminar cada tarea.

## Verificación

- Correr `pytest -v` desde la raíz y confirmar que pasa antes de dar una tarea por terminada.
- Opcional: con `uvicorn` corriendo, los endpoints nuevos o modificados también se pueden comprobar con el MCP de Chrome DevTools abriendo `http://localhost:8000/docs` (o la URL del endpoint) en http://localhost:8000.
