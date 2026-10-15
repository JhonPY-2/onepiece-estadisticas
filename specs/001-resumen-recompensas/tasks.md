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

- [ ] **T2. Helpers de normalización y promedio con tests unitarios.** RF-4, RF-5
  - Tests: crear `tests/test_recompensas_resumen.py` con `NOMBRE_DB_TEST = "onepiece_test"` y tests unitarios de `normalizar_recompensa` (`None→0`, `1000→1000`, `1.5→2`, `2.4→2`, `1500.7→1501`, `0→0`) y de `promedio_recompensas` (`(3,2)→2`, `(2,2)→1`, `(5,2)→3`, `(0,3)→0`, `(4,3)→1`, `(10,0)→0`). Deben quedar en rojo (las funciones aún no existen).
  - Código: en `main.py`, bloque de helpers de agregación, definir `normalizar_recompensa(valor)` (ausente/`None`→`0`; `int` tal cual; no entero → `math.floor(v + 0.5)`) y `promedio_recompensas(total, cantidad)` (`0` si `cantidad == 0`; si no `(total + cantidad // 2) // cantidad`), sin `float`/`Decimal`.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_recompensas_resumen.py -k "normalizar or promedio" -v` pasa en verde.

- [ ] **T3. Modelo de respuesta y endpoint con colección vacía.** RF-1, RF-2, RF-8, RF-9
  - Tests: en `tests/test_recompensas_resumen.py`, tests de integración con las fixtures `db_test`/`cliente_http` (definidas en `tests/conftest.py`): `GET /estadisticas/recompensas/resumen` con colección vacía → `200` y los cinco campos en `0`; claves exactas `{cantidad_personajes, total_recompensas, promedio_recompensa, recompensa_maxima, recompensa_minima}` sin extras; `POST` y `PUT` a la misma ruta → `405`.
  - Código: en `main.py`, modelo `RecompensasResumen(BaseModel)` con `ConfigDict(extra="forbid")` y los 5 campos `int`; endpoint `@app.get("/estadisticas/recompensas/resumen", response_model=RecompensasResumen)` que recorre `db.personajes.find({}, {"recompensa": 1})` y, si no hay documentos, devuelve los cinco ceros. No tocar `/estadisticas/resumen`.
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200`, `Content-Type: application/json` y JSON con **exactamente** esos 5 campos; el endpoint aparece en `http://localhost:8000/docs`. El `405` de `POST`/`PUT` se verifica solo con los tests. Tests en verde.

- [ ] **T4. Contar personajes y agregar total, máxima y mínima.** RF-3, RF-4, RF-6, RF-7
  - Tests: con datos en `personajes`: dos recompensas enteras (Luffy `3000000000`, Zoro `1000000000`) → `cantidad_personajes=2`, `total_recompensas=4000000000`, `recompensa_maxima=3000000000`, `recompensa_minima=1000000000`; `recompensa: 0` participa (`min=0`); `null`/ausente cuenta como `0`; no entero se redondea **antes** de agregar (`1.5→2`, `2.4→2` → `total=4`, `max=2`).
  - Código: en el endpoint, dentro del recorrido del cursor, incrementar contador y acumular `total`, `recompensa_maxima` y `recompensa_minima` usando `normalizar_recompensa` (inicializar max/min con el primer valor).
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200` con los valores coherentes y que coinciden con lo que muestra el `GET /estadisticas/personajes` existente (solo lectura), y `recompensa_maxima` es un **número** (sin nombre); tests en verde.

- [ ] **T5. Calcular el promedio con aritmética entera.** RF-5
  - Tests: `{1, 2}` (total 3, 2 personajes) → `promedio_recompensa=2`; `{0, 5}` → `3`; caso entero `{3000000000, 1000000000}` → `2000000000`.
  - Código: en el endpoint, calcular `promedio_recompensa = promedio_recompensas(total, contador)` y devolver el modelo con los cinco enteros.
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200` con `promedio_recompensa` entero y coherente con lo que muestra el `GET /estadisticas/personajes` existente (solo lectura), no `float`; tests en verde.

- [ ] **T6. Casos límite: sin recompensas y un solo personaje.** RF-3, RF-4, RF-5, RF-6, RF-7
  - Tests: 3 personajes sin `recompensa`/`null` → `cantidad_personajes=3` y los otros cuatro campos en `0`; un único personaje `1500.7` → los cinco campos coherentes con `1501`; un único personaje sin recompensa → `cantidad=1` y resto `0`.
  - Código: sin cambios de código esperados; si algún test falla, corregir la inicialización de `recompensa_maxima`/`recompensa_minima`.
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/recompensas/resumen` responde `200` con los 5 campos y valores coherentes con lo que muestra el `GET /estadisticas/personajes` existente (solo lectura) en cada caso; tests en verde.

- [ ] **T7. Regresión: `/estadisticas/resumen` no cambia.** Criterios de finalización
  - Tests: `GET /estadisticas/resumen` con datos → sigue devolviendo `200` y su estructura propia (`total_personajes`, `total_atletas`, `personaje_mayor_recompensa`) sin campos nuevos.
  - Código: ninguno en `/estadisticas/resumen`; confirmar que solo se añadió el nuevo endpoint.
  - Hecho cuando: Chrome DevTools → `GET http://localhost:8000/estadisticas/resumen` responde `200` con su forma original; test en verde.

- [ ] **T8. Verificación final de contrato y criterios de finalización.** RF-1–RF-9
  - Tests: correr la suite completa y confirmar que todos los RF y criterios de la spec se cumplen.
  - Código: ninguno.
  - Hecho cuando: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` pasa en verde y Chrome DevTools confirma en `/docs` y en `GET /estadisticas/recompensas/resumen` el código `200` y los 5 campos exactos.
