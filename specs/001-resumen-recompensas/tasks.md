# Tasks: specs/001-resumen-recompensas/tasks.md

**Estado: aprobada**

**Spec de referencia:** [`specs/001-resumen-recompensas/spec.md`](./spec.md) – aprobada.
**Plan:** [`specs/001-resumen-recompensas/plan.md`](./plan.md).

Comando de tests (usuario, PowerShell):
`$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v`
Contrato HTTP: Chrome DevTools **solo lectura** contra `http://localhost:8000` (GET y `/docs`). El agente no ejecuta pytest ni uvicorn.

## Tareas

- [x] **T1. Mover las fixtures compartidas a `conftest.py`.** (Preparación, sin RF nuevos)
  - Tests: sin tests nuevos; debe seguir pasando toda la suite existente.
  - Código: mover `NOMBRE_DB_TEST`, la fixture `db_test` y la fixture `cliente_http` desde `tests/test_estadisticas.py` a `tests/conftest.py` sin cambiar su comportamiento; `tests/test_estadisticas.py` debe seguir funcionando (las fixtures pasan a estar disponibles para cualquier archivo de `tests/`).
  - Hecho cuando: el usuario corre `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` y pasan los mismos tests que antes, sin tests nuevos.

- [x] **T2. Helpers de normalización y promedio con tests unitarios.** RF-4, RF-5
  - Tests: crear `tests/test_recompensas_resumen.py` con `NOMBRE_DB_TEST = "onepiece_test"` y tests unitarios de `normalizar_recompensa` (`None→0`, `1000→1000`, `1.5→2`, `2.4→2`, `1500.7→1501`, `0→0`) y de `promedio_recompensas` (`(3,2)→2`, `(2,2)→1`, `(5,2)→3`, `(0,3)→0`, `(4,3)→1`, `(10,0)→0`). Deben quedar en rojo (las funciones aún no existen).
  - Código: en `main.py`, bloque de helpers de agregación, definir `normalizar_recompensa(valor)` (ausente/`None`→`0`; `int` tal cual; no entero → `math.floor(v + 0.5)`) y `promedio_recompensas(total, cantidad)` (`0` si `cantidad == 0`; si no `(total + cantidad // 2) // cantidad`), sin `float`/`Decimal`.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_recompensas_resumen.py -k "normalizar or promedio" -v` pasa en verde.

- [x] **T3. Modelo de respuesta y endpoint con colección vacía.** RF-1, RF-2, RF-8, RF-9
  - Tests: en `tests/test_recompensas_resumen.py`, tests de integración con las fixtures `db_test`/`cliente_http` (definidas en `tests/conftest.py`): `GET /estadisticas/recompensas/resumen` con colección vacía → `200` y los cinco campos en `0`; claves exactas `{cantidad_personajes, total_recompensas, promedio_recompensa, recompensa_maxima, recompensa_minima}` sin extras; `POST` y `PUT` a la misma ruta → `405`.
  - Código: en `main.py`, modelo `RecompensasResumen(BaseModel)` con `ConfigDict(extra="forbid")` y los 5 campos `int`; endpoint `@app.get("/estadisticas/recompensas/resumen", response_model=RecompensasResumen)` que recorre `db.personajes.find({}, {"recompensa": 1})` y, si no hay documentos, devuelve los cinco ceros. No tocar `/estadisticas/resumen`.
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200`, `Content-Type: application/json` y JSON con **exactamente** esos 5 campos; el endpoint aparece en `http://localhost:8000/docs`. El `405` de `POST`/`PUT` se verifica solo con los tests. Tests en verde.
  - Completada y verificada: pytest 25 passed; en `/docs` aparece `GET /estadisticas/recompensas/resumen` y el GET devuelve JSON con los cinco campos enteros (verificado a mano en el navegador; el MCP de DevTools no está disponible en esta sesión).
  - Nota (adelanto de T4/T5): **en T3 se adelantó también la lógica de agregación** (`total_recompensas`, `recompensa_maxima`, `recompensa_minima` y `promedio_recompensa`) que correspondía a T4 y T5; el endpoint ya la calcula recorriendo el cursor. Por eso **T4 y T5 ahora solo aportan los tests** que cubren esa lógica; no requieren cambios de código salvo que un test detecte un fallo.

- [x] **T4. Contar personajes y agregar total, máxima y mínima.** RF-3, RF-4, RF-6, RF-7
  - Nota (adelanto desde T3): el código de esta tarea (conteo, `total`, `recompensa_maxima` y `recompensa_minima`) **ya se implementó en T3**; esta tarea ahora aporta los tests que lo cubren.
  - Tests: con datos en `personajes`: dos recompensas enteras (Luffy `3000000000`, Zoro `1000000000`) → `cantidad_personajes=2`, `total_recompensas=4000000000`, `recompensa_maxima=3000000000`, `recompensa_minima=1000000000`; `recompensa: 0` participa (`min=0`); `null`/ausente cuenta como `0`; no entero se redondea **antes** de agregar (`1.5→2`, `2.4→2` → `total=4`, `max=2`).
  - Código: en el endpoint, dentro del recorrido del cursor, incrementar contador y acumular `total`, `recompensa_maxima` y `recompensa_minima` usando `normalizar_recompensa` (inicializar max/min con el primer valor).
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200` con los valores coherentes y que coinciden con lo que muestra el `GET /estadisticas/personajes` existente (solo lectura), y `recompensa_maxima` es un **número** (sin nombre); tests en verde.

- [x] **T5. Calcular el promedio con aritmética entera.** RF-5
  - Nota (adelanto desde T3): el cálculo de `promedio_recompensa` con aritmética entera **ya se implementó en T3**; esta tarea ahora aporta los tests que lo cubren.
  - Tests: `{1, 2}` (total 3, 2 personajes) → `promedio_recompensa=2`; `{0, 5}` → `3`; caso entero `{3000000000, 1000000000}` → `2000000000`.
  - Código: en el endpoint, calcular `promedio_recompensa = promedio_recompensas(total, contador)` y devolver el modelo con los cinco enteros.
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200` con `promedio_recompensa` entero y coherente con lo que muestra el `GET /estadisticas/personajes` existente (solo lectura), no `float`; tests en verde.
  - Completada y verificada: pytest 22 passed; los 3 tests de promedio a nivel de endpoint pasan en verde sin que antes estuvieran en rojo porque la lógica (función `promedio_recompensas` y su uso en el endpoint) ya existía desde T3; no hubo cambios en `main.py`.

- [x] **T6. Casos límite: sin recompensas y un solo personaje.** RF-3, RF-4, RF-5, RF-6, RF-7
  - Tests: 3 personajes sin `recompensa`/`null` → `cantidad_personajes=3` y los otros cuatro campos en `0`; un único personaje `1500.7` → los cinco campos coherentes con `1501`; un único personaje sin recompensa → `cantidad=1` y resto `0`.
  - Código: sin cambios de código esperados; la inicialización de `recompensa_maxima`/`recompensa_minima` en T3 ya cubría el caso (primera iteración).
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200` con los 5 campos y valores coherentes con lo que muestra el `GET /estadisticas/personajes` existente (solo lectura) en cada caso; tests en verde.
  - Completada y verificada: `tests/test_recompensas_resumen.py` - 25 passed en verde a la primera; los 3 tests de T6 pasan porque la lógica de T3-T5 ya cubría los casos límite (sin recompensas y un solo personaje). No se modificó `main.py`.

- [x] **T7. Regresión: `/estadisticas/resumen` no cambia.** Criterios de finalización
  - Tests: `GET /estadisticas/resumen` con datos → sigue devolviendo `200` y su estructura propia (`total_personajes`, `total_atletas`, `personaje_mayor_recompensa`) sin campos nuevos.
  - Código: ninguno en `/estadisticas/resumen`; confirmar que solo se añadió el nuevo endpoint.
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/resumen` responde `200` con su forma original; test en verde.
  - Completada y verificada: añadido test de regresión `test_estadisticas_resumen_regresion_sin_campos_nuevos` en `tests/test_recompensas_resumen.py`; los 36 tests (`tests/test_recompensas_resumen.py` + `tests/test_estadisticas.py`) pasaron en verde a la primera, porque `/estadisticas/resumen` no se modificó. No se tocó `main.py`.

- [x] **T8. Verificación final de contrato y criterios de finalización.** RF-1–RF-9
  - Tests: correr la suite completa y confirmar que todos los RF y criterios de la spec se cumplen.
  - Código: ninguno.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` pasa en verde y Chrome DevTools confirma en `/docs` y en `GET /estadisticas/recompensas/resumen` el código `200` y los 5 campos exactos.
  - Completada y verificada: suite completa **36 passed** (`tests/test_recompensas_resumen.py` + `tests/test_estadisticas.py`). En `/docs` aparece `GET /estadisticas/recompensas/resumen` junto a `/estadisticas/resumen`. Verificación manual en navegador (solo lectura): `GET http://localhost:8000/estadisticas/recompensas/resumen` → código `200`, `Content-Type: application/json`, exactamente 5 campos enteros: `cantidad_personajes=20`, `total_recompensas=14451509000`, `promedio_recompensa=722575450` (coincide con total/cantidad), `recompensa_maxima=3996000000`, `recompensa_minima=1000`. `POST` y `PUT` → `405` verificados por los tests (no por navegador). No se tocó `main.py` ni ningún test.

- [x] **T9. Tests primero para RF-10 y actualización de tests existentes.** RF-10
  - Tests: Añadir test que cubre la mezcla `0`/`null`/ausente/`0.4` (4 de 5 personajes sin recompensa → `personajes_sin_recompensa = 4`) y el caso "sin ninguna recompensa" con `personajes_sin_recompensa == cantidad_personajes`. Actualizar los tests existentes que esperan exactamente cinco campos para que esperen **seis** campos (`personajes_sin_recompensa` incluido) y sus claves exactas. Estos tests deben quedar en **rojo** (aún no se toca `main.py`).
  - Código: No tocar `main.py` en esta tarea. Modificar solo los archivos de tests (`tests/test_recompensas_resumen.py` y otros si existen) siguiendo las convenciones.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_recompensas_resumen.py -v` falla (al menos los tests que exigen seis campos) y el fallo es claramente por la ausencia del sexto campo o por la espera de cinco campos; no se ha modificado `main.py`.
  - Completada y verificada: añadidos 3 tests nuevos (`test_recompensas_estructura_solo_seis_campos`, `test_recompensas_mezcla_cero_null_ausente_y_0_4`, `test_recompensas_resumen_sin_ninguna_recompensa`) y actualizados 2 existentes (colección vacía y sin recompensas) a seis campos en `tests/test_recompensas_resumen.py`. Corrido por el usuario: **5 failed, 24 passed** en rojo **a propósito** (todos `AssertionError` por falta de `personajes_sin_recompensa`), sin tocar `main.py`.

- [x] **T10. Modelo de seis campos y contador en el recorrido hasta verde.** RF-10
  - Tests: Los tests añadidos/actualizados en T9 ya existen (pero fallan); esta tarea hace pasar esos tests.
  - Código: Añadir `personajes_sin_recompensa: int` al modelo `RecompensasResumen` (manteniendo `extra="forbid"`). En el endpoint, inicializar `personajes_sin_recompensa = 0` (o `sin_recompensa`), contar en el mismo recorrido del cursor: cuando `recompensa_norm == 0` se incrementa el contador (incluye `0`, `null`, ausente y valores que redondean a `0`). Si `cantidad_personajes == 0`, devolver seis campos a `0`. Si `cantidad_personajes > 0`, incluir `personajes_sin_recompensa` en la respuesta. No realizar una segunda consulta.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_recompensas_resumen.py -v` pasa en verde; `main.py` solo se ha modificado para añadir el sexto campo y el contador del mismo recorrido.
  - Completada y verificada: corrido por el usuario tras T10 → **39 passed** (suite completa; los 5 en rojo por T9 ya pasan). `git diff` de `main.py` = 7 líneas añadidas (campo `personajes_sin_recompensa` en el modelo, contador inicial, `if recompensa_norm == 0` dentro del bucle y el campo en los dos `return`). No se tocaron tests, spec ni plan.

- [ ] **T11. Verificación final: suite completa en verde, /docs y GET real en solo lectura con seis campos.** RF-1–RF-10
  - Tests: Correr la suite completa.
  - Código: Ninguno (o mínimos ajustes si algún test ajeno falla).
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` pasa en verde. Chrome DevTools confirma en `/docs` y en `GET /estadisticas/recompensas/resumen` el código `200` y **exactamente seis campos enteros** (`cantidad_personajes`, `total_recompensas`, `promedio_recompensa`, `recompensa_maxima`, `recompensa_minima`, `personajes_sin_recompensa`). La verificación del GET es **solo lectura**. No se ha modificado `/estadisticas/resumen`. No se tocan otros archivos fuera de los necesarios para que la suite pase.
