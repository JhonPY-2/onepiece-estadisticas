# Tasks: specs/002-personajes-sin-tripulacion/tasks.md

**Estado: aprobada**

**Spec de referencia:** [`specs/002-personajes-sin-tripulacion/spec.md`](./spec.md) – aprobada.
**Plan:** [`specs/002-personajes-sin-tripulacion/plan.md`](./plan.md).

Comando de tests (usuario, PowerShell):
`$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v`
Contrato HTTP: Chrome DevTools **solo lectura** contra `http://localhost:8000` (GET y `/docs`). El agente no ejecuta pytest ni uvicorn.

## Tareas

- [ ] **T1. Tests de contrato y colección vacía (rojo).** RF-1, RF-2, RF-5, RF-6
  - Tests: crear `tests/test_personajes_sin_tripulacion.py` con `NOMBRE_DB_TEST = "onepiece_test"` a nivel de módulo (lo exige el guard de `tests/conftest.py`) y las fixtures `db_test`/`cliente_http`. Añadir: `test_personajes_sin_tripulacion_coleccion_vacia` (`GET` con colección vacía → `200` y `{"cantidad": 0}`), `test_personajes_sin_tripulacion_estructura_solo_cantidad` (con un `{"nombre": "A"}` → `200`, `set(datos.keys()) == {"cantidad"}` y `isinstance(datos["cantidad"], int)`), `test_personajes_sin_tripulacion_post_no_permitido` (`POST` → `405`) y `test_personajes_sin_tripulacion_put_no_permitido` (`PUT` → `405`). Deben quedar en **rojo** (el endpoint aún no existe → `404`).
  - Código: ninguno en esta tarea.
  - Hecho cuando: el usuario corre `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_personajes_sin_tripulacion.py -v` y los tests de `GET` fallan por endpoint inexistente (`404`), sin haberse tocado `main.py`.

- [ ] **T2. Modelo y endpoint con el conteo.** RF-1, RF-2, RF-3, RF-4, RF-5, RF-6, RF-7
  - Tests: los de T1 ya existen y deben pasar a verde con esta tarea.
  - Código: en `main.py`, bloque de modelos Pydantic (junto a `RecompensasResumen`, `main.py:60-68`), añadir `class PersonajesSinTripulacion(BaseModel)` con `model_config = {"extra": "forbid"}` y el campo `cantidad: int`. En el bloque de endpoints (`main.py:97` en adelante), añadir `@app.get("/estadisticas/personajes/sin-tripulacion", response_model=PersonajesSinTripulacion)` con `cantidad = await db.personajes.count_documents({"tripulacion": None})` y `return {"cantidad": cantidad}`. No modificar ningún endpoint existente.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_personajes_sin_tripulacion.py -v` pasa en verde; `main.py` solo se ha modificado para añadir el modelo y el endpoint nuevos.

- [ ] **T3. Tests de conteo y casos límite.** RF-3, RF-4, RF-7
  - Tests: en `tests/test_personajes_sin_tripulacion.py`, añadir con datos en `personajes` (usando los `ObjectId` del patrón de `tests/test_estadisticas.py:19-21`): `test_personajes_sin_tripulacion_mezcla` (2 con `tripulacion` `ObjectId` + 2 sin (`None` y campo ausente) → `{"cantidad": 2}`), `test_personajes_sin_tripulacion_campo_ausente_y_null` (ausente + `None` → `{"cantidad": 2}`), `test_personajes_sin_tripulacion_objectid_sin_documento_no_cuenta` (`ObjectId` sin documento → `{"cantidad": 0}`; puede usar un `ObjectId` sin documento como el de `tests/test_estadisticas.py:21` (`ID_SIN_DOCUMENTO = ObjectId("000000000000000000000001")`) o crear uno equivalente en su propio archivo), `test_personajes_sin_tripulacion_cadena_vacia_cuenta_como_con` (`tripulacion: ""` → `{"cantidad": 0}`), `test_personajes_sin_tripulacion_ignora_tripulantes` (1 en `personajes` sin tripulación + 2 en `tripulantes` sin tripulación → `{"cantidad": 1}`), `test_personajes_sin_tripulacion_todos_con_tripulacion` (2 con `ObjectId` → `{"cantidad": 0}`) y `test_personajes_sin_tripulacion_unico_sin_tripulacion` (`{"nombre": "A"}` → `{"cantidad": 1}`). Comparar el JSON completo (`res.json() == {"cantidad": n}`).
  - Código: sin cambios esperados (el filtro `{"tripulacion": None}` de T2 cubre estos casos); ajustar `main.py` solo si algún test detecta un fallo.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_personajes_sin_tripulacion.py -v` pasa en verde con los 11 tests.

- [ ] **T4. Regresión y verificación final de contrato.** RF-1–RF-7 y criterios de finalización
  - Tests: correr la suite completa y confirmar que `tests/test_estadisticas.py` y `tests/test_recompensas_resumen.py` siguen pasando sin cambios (los endpoints existentes no cambian su comportamiento ni su contrato).
  - Código: ninguno.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` pasa en verde; con el servidor levantado, Chrome DevTools (solo lectura) confirma en `http://localhost:8000/docs` la aparición de `GET /estadisticas/personajes/sin-tripulacion` y en `GET http://localhost:8000/estadisticas/personajes/sin-tripulacion` el código `200` con `Content-Type: application/json` y un cuerpo `{"cantidad": <entero >= 0>}` con exactamente ese campo.
