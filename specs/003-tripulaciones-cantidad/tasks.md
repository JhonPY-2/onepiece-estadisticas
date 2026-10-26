# Tasks: specs/003-tripulaciones-cantidad/tasks.md

**Estado: aprobada**

**Spec de referencia:** [`specs/003-tripulaciones-cantidad/spec.md`](./spec.md) – aprobada.
**Plan:** [`specs/003-tripulaciones-cantidad/plan.md`](./plan.md).

Comando de tests (usuario, PowerShell):
`$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v`
Contrato HTTP: Chrome DevTools **solo lectura** contra `http://localhost:8000` (GET y `/docs`). El agente no ejecuta pytest ni uvicorn.

## Tareas

- [x] **T1. Tests de contrato y colección vacía (rojo).** RF-1, RF-2, RF-5, RF-6
  - Tests: crear `tests/test_tripulaciones_cantidad.py` con `NOMBRE_DB_TEST = "onepiece_test"` a nivel de módulo (lo exige el guard de `tests/conftest.py`) y las fixtures `db_test`/`cliente_http`. Añadir: `test_tripulaciones_cantidad_coleccion_vacia` (colección `tripulaciones` vacía → `GET /estadisticas/tripulaciones/cantidad` → `200` y `{"cantidad": 0}`), `test_tripulaciones_cantidad_estructura_solo_cantidad` (con 1 documento en `tripulaciones` → `200`, `set(datos.keys()) == {"cantidad"}` y `isinstance(datos["cantidad"], int)`), `test_tripulaciones_cantidad_post_no_permitido` (`POST` → `405`) y `test_tripulaciones_cantidad_put_no_permitido` (`PUT` → `405`). Deben quedar en **rojo** (el endpoint aún no existe → `404`).
  - Código: ninguno en esta tarea.
  - Hecho cuando: el usuario corre `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_tripulaciones_cantidad.py -v` y los tests de `GET` fallan por endpoint inexistente (`404`), sin haberse tocado `main.py`.

- [x] **T2. Modelo y endpoint con el conteo (verde).** RF-1, RF-2, RF-3, RF-5, RF-6, RF-7
  - Tests: los de T1 ya existen y deben pasar a verde con esta tarea.
  - Código: en `main.py`, bloque de modelos Pydantic (junto a `PersonajesSinTripulacion`, `main.py:71-75`), añadir `class TripulacionesCantidad(BaseModel)` con `model_config = {"extra": "forbid"}` y el campo `cantidad: int`. En el bloque de endpoints (después de `/estadisticas/personajes/sin-tripulacion`), añadir `@app.get("/estadisticas/tripulaciones/cantidad", response_model=TripulacionesCantidad)`. Implementar: `existentes = await db.list_collection_names()`, se usa el helper `coleccion_tripulaciones(existentes)`, se obtiene la colección resuelta y se hace `count_documents({})` sobre ella; no se duplica la lógica de decidir entre candidatas. Si no existe ninguna colección candidata, el conteo sobre la colección inexistente da 0 por sí solo, sin rama especial en el código. Reutilizar el helper `coleccion_tripulaciones()` sin duplicar lógica. No modificar ningún endpoint existente.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_tripulaciones_cantidad.py -v` pasa en verde; `main.py` solo se ha modificado para añadir el modelo y el endpoint nuevos.

- [ ] **T3. Tests de conteo, miembros y resolución de colección (verde).** RF-3, RF-4, RF-7
  - Tests: en `tests/test_tripulaciones_cantidad.py`, añadir: `test_tripulaciones_cantidad_cuenta_documentos_no_miembros` (3 documentos en colección de tripulaciones + miembros en `personajes`/`tripulantes` → `{"cantidad": 3}`), `test_tripulaciones_cantidad_sin_coleccion_candidata` (sin `tripulaciones` ni `tripulacions` → `200` + `{"cantidad": 0}`), `test_tripulaciones_cantidad_usa_tripulacions` (solo `tripulacions` con n documentos → `{"cantidad": n}`), `test_tripulaciones_cantidad_ignora_personajes_tripulantes` (solo colección resuelta con documentos, `personajes`/`tripulantes` con muchos documentos → conteo solo de documentos de tripulaciones), `test_tripulaciones_cantidad_tripulaciones_sin_miembros` (tripulaciones sin miembros apuntando → conteo correcto), `test_tripulaciones_cantidad_unica_tripulacion` (1 documento → `{"cantidad": 1}`), `test_tripulaciones_cantidad_existen_ambas_candidatas` (existen `tripulaciones` y `tripulacions` a la vez; se cuenta la misma que cuenta `/estadisticas/tripulaciones`, usando datos propios en `onepiece_test`; RF-7), `test_tripulaciones_cantidad_parametro_consulta_ignorado` (se envía un parámetro de consulta en la petición y se ignora sin error, RF-1 y RF-2; datos propios en `onepiece_test`). Comparar JSON completo (`res.json() == {"cantidad": n}`).
  - Código: sin cambios esperados si T2 es correcto; ajustar `main.py` solo si algún test detecta fallo.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_tripulaciones_cantidad.py -v` pasa en verde con todos los tests de este archivo.

- [ ] **T4. Regresión y verificación final de contrato.** RF-1–RF-7 y criterios de finalización
  - Tests: correr la suite completa y confirmar que `tests/test_estadisticas.py`, `tests/test_recompensas_resumen.py` y `tests/test_personajes_sin_tripulacion.py` siguen pasando sin cambios (los endpoints existentes no cambian su comportamiento ni su contrato).
  - Código: ninguno.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` pasa en verde; con servidor levantado, Chrome DevTools (solo lectura) confirma en `http://localhost:8000/docs` la aparición de `GET /estadisticas/tripulaciones/cantidad` y en `GET http://localhost:8000/estadisticas/tripulaciones/cantidad` el código `200` with `Content-Type: application/json` and `{"cantidad": <entero >= 0>}` con exactamente ese campo.

## Pendientes / Preguntas (resueltas)

- (a) Contar en una colección inexistente no la crea, porque contar solo lee.
- (b) Tripulaciones sin campo nombre: el endpoint nuevo cuenta documentos y no lee ese campo.
- (c) Base caída o colección inaccesible: sin manejo especial de errores, como en los demás endpoints (comprobado en main.py: ningún endpoint captura excepciones de la base). No se prueba porque la constitución exige Mongo real.
