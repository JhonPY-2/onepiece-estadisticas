# Plan: `specs/002-personajes-sin-tripulacion/plan.md`

**Spec de referencia:** [`specs/002-personajes-sin-tripulacion/spec.md`](./spec.md) – **Estado: aprobada**. No quedan dudas abiertas ni entradas `[NECESITA ACLARACIÓN]`.

## 1. Objetivo y alcance

Añadir un nuevo endpoint **de solo lectura** `GET /estadisticas/personajes/sin-tripulacion` que devuelva únicamente un JSON con un único campo `cantidad` (entero `>= 0`), igual al número de documentos de la colección `personajes` cuyo campo `tripulacion` **no existe** o vale `null` (RF-1–RF-7).

- **Complementa** (no reemplaza ni modifica) a `/estadisticas/personajes`, `/estadisticas/atletas`, `/estadisticas/tripulaciones`, `/estadisticas/resumen` y `/estadisticas/recompensas/resumen`.
- Reutiliza la arquitectura existente: `main.py` (app FastAPI, modelos Pydantic y endpoints), conexión Mongo asíncrona vía Motor y la colección `personajes` (`db.personajes`).
- Un valor de `tripulacion` presente y distinto de `null` (p. ej. un `ObjectId`, aunque su documento no exista en la colección de tripulaciones, o una cadena vacía `""`) cuenta como **con** tripulación y NO entra en `cantidad` (decisión recogida en las Definiciones de la spec).
- El conteo es **solo** de `personajes`; no mira `tripulantes` ni la colección de tripulaciones (RF-7).
- Tests de integración con `pytest + pytest-asyncio + httpx` contra Mongo real, usando **siempre** la base `onepiece_test`.
- Verificación de contrato HTTP vía Chrome DevTools (solo lectura) contra `http://localhost:8000` (`/docs` y la URL del endpoint).

El agente **NO** ejecuta pytest ni arranca uvicorn: los corre el usuario desde PowerShell.

## 2. Archivos a crear/modificar y responsabilidades

| Archivo | Acción | Responsabilidades |
|---|---|---|
| [`main.py`](../../main.py) | **Modificar** | En el bloque de modelos Pydantic (`main.py:20-68`) añadir un modelo estricto `PersonajesSinTripulacion(BaseModel)` con `model_config = {"extra": "forbid"}` y un único campo `cantidad: int` (mismo estilo que `RecompensasResumen`, `main.py:60-68`). En el bloque de endpoints (`main.py:97` en adelante) añadir `@app.get("/estadisticas/personajes/sin-tripulacion", response_model=PersonajesSinTripulacion)` que cuente los documentos de `db.personajes` con `tripulacion` ausente o `null` y devuelva `{"cantidad": <int>}`. Reutiliza el `db` global (`main.py:17`) y la colección `personajes` ya usada por `estadisticas_personajes` (`main.py:141-159`). **No** tocar ningún endpoint existente ni el bloque de helpers de agregación. |
| [`tests/test_personajes_sin_tripulacion.py`](../../tests/test_personajes_sin_tripulacion.py) | **Crear** | Tests de integración (pytest + pytest-asyncio + httpx) que cubren todos los RF y los casos límite de la spec: colección vacía (RF-5), estructura exacta de un solo campo `cantidad` entero (RF-2, RF-6), métodos no GET → `405` (caso límite), mezcla con/sin tripulación (RF-3, RF-4), campo `tripulacion` ausente y `null` (RF-4), `ObjectId` sin documento correspondiente **no** cuenta (RF-4), cadena vacía `""` **no** cuenta (RF-4), `tripulantes` ignorado (RF-7), todos con tripulación → `0` y un único personaje sin tripulación → `1` (RF-3). Inserta datos directamente en Mongo y llama al endpoint vía la fixture `cliente_http`. Debe declarar `NOMBRE_DB_TEST = "onepiece_test"` a nivel de módulo para pasar el guard de [`tests/conftest.py`](../../tests/conftest.py). **No usan** la base `onepiece`. |

**Archivos que NO se tocan:**
- [`tests/conftest.py`](../../tests/conftest.py): ya expone las fixtures `db_test` y `cliente_http`, que cualquier archivo de `tests/` puede usar; no hace falta modificarlo.
- [`tests/test_estadisticas.py`](../../tests/test_estadisticas.py) y [`tests/test_recompensas_resumen.py`](../../tests/test_recompensas_resumen.py): solo se usan como referencia de estilo y como regresión.

**Notas de arquitectura:**
- `main.py` ya contiene `app = FastAPI()` (`main.py:14`), el cliente Motor y `db = cliente.get_default_database()` (`main.py:16-17`), los modelos Pydantic y los endpoints. Se mantiene el estilo existente (bloques separados, `@app.get`, `response_model`).
- No se añaden dependencias (Motor/Pydantic ya están en `requirements.txt`). No hay lint ni build.
- La ruta nueva `/estadisticas/personajes/sin-tripulacion` es un segmento fijo adicional al de `/estadisticas/personajes` (`main.py:141`); al no existir ningún path param en esa ruta, no hay conflicto de enrutado en FastAPI.

## 3. Lógica (algoritmo/pseudocódigo) que cubre todos los RF

### 3.1 Modelo Pydantic de respuesta

Definir un modelo estricto para el `response_model` (garantiza un único campo, tipo entero y ausencia de campos extra):

```python
class PersonajesSinTripulacion(BaseModel):
    model_config = {"extra": "forbid"}
    cantidad: int
```

(RF-2, RF-6)

### 3.2 Conteo de personajes sin tripulación asignada

La spec define "sin tripulación asignada" como el documento de `personajes` cuyo campo `tripulacion` **no existe** o vale **`null`** (Definiciones). En MongoDB, el filtro `{"tripulacion": None}` hace exactamente eso: coincide tanto con documentos donde el campo no existe como con documentos donde el valor es `null`. Cualquier otro valor (un `ObjectId`, una cadena vacía `""`, etc.) **no** coincide con ese filtro y por tanto se considera **con** tripulación.

Endpoint: `GET /estadisticas/personajes/sin-tripulacion` (RF-1)

```text
1. cantidad = await db.personajes.count_documents({"tripulacion": None})
2. return {"cantidad": cantidad}
```

- `db.personajes` es la **única** colección consultada (RF-7); no se consulta `tripulantes` ni la colección de tripulaciones.
- `count_documents` devuelve siempre un `int >= 0`: `0` con colección vacía (RF-5) o cuando todos los personajes tienen tripulación, y el total de documentos cuando ninguno la tiene (RF-3, RF-6).
- No se resuelve la existencia del documento referenciado: un `ObjectId` presente en `tripulacion` no coincide con `{"tripulacion": None}`, así que no se cuenta (RF-4).
- Lectura pura: no se crea, modifica ni borra nada (RNF-1).

### 3.3 Cobertura de los RF

- RF-1: el endpoint `@app.get(...)` responde `200` con el modelo.
- RF-2: el modelo con `extra="forbid"` y un solo campo `cantidad` produce un JSON con exactamente ese campo.
- RF-3: `count_documents` cuenta exactamente los documentos de `personajes` que cumplen el filtro.
- RF-4: `{"tripulacion": None}` incluye ausente y `null`; excluye cualquier otro valor (incl. `ObjectId` sin documento y `""`).
- RF-5: con la colección vacía, `count_documents` devuelve `0`.
- RF-6: `count_documents` siempre devuelve `int >= 0`, nunca `null`, negativo ni texto.
- RF-7: se consulta solo `db.personajes`.

## 4. Decisiones técnicas justificadas

| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| **Añadir el endpoint en `main.py`** (no crear módulo/router nuevo) | Proyecto pequeño (microservicio único); mantiene coherencia con los endpoints existentes (`main.py:141-280`) y evita estructura innecesaria. | Crear `routers/personajes.py` y registrarlo: añade capas y complejidad de imports para un único endpoint. |
| **Modelo `PersonajesSinTripulacion` con `model_config = {"extra": "forbid"}`** | Garantiza el contrato estricto de RF-2 (exactamente el campo `cantidad`) y que `cantidad` sea entero (RF-6), siguiendo el estilo ya usado por `RecompensasResumen` (`main.py:60-68`). | Devolver un `dict` sin `response_model`: no valida la forma exacta ni el tipo, y permitiría campos accidentales. |
| **Filtro `{"tripulacion": None}` con `count_documents`** | En MongoDB `{"campo": None}` coincide con ausente y con `null` (justo la definición de RF-4) y excluye cualquier otro valor (incluido `ObjectId` sin documento y `""`). Es una sola operación de conteo, simple y determinista (RNF-2). | `$group`/`$match` con `$exists` y `$or` o un `find` + conteo en Python: más código sin aportar nada; `$or: [{"tripulacion": {"$exists": False}}, {"tripulacion": None}]` es equivalente pero más verboso. |
| **No resolver la colección de tripulaciones** | La spec (Definiciones y RF-4) dice que la asignación se mira en el propio personaje: un `ObjectId` presente cuenta como con tripulación aunque su documento no exista. | Hacer `$lookup` contra la colección de tripulaciones para comprobar existencia: contradice RF-4 y añade coste; además la colección no siempre está presente. |
| **Contar solo `db.personajes`** | La ruta es `/estadisticas/personajes/sin-tripulacion` y RF-7 lo exige; `tripulantes` queda fuera. | Contar `personajes` + `tripulantes`: no lo pide la spec y cambiaría el resultado. |
| **Tests de integración con `httpx.ASGITransport` + datos en Mongo real (`onepiece_test`)** | Siguen el patrón existente: fixtures `db_test` y `cliente_http` de [`tests/conftest.py`](../../tests/conftest.py), con `monkeypatch` de `main.db` y limpieza de `onepiece_test`. Reflejan el comportamiento real de Motor. | Mockear la base de datos: no valida la interacción real ni el aislamiento. |
| **Contrato HTTP con Chrome DevTools (solo lectura)** | Cumple el requisito del flujo: comprobar método, ruta, código `200` y forma exacta del JSON en `/docs` y en la URL del endpoint. | Solo tests: no validan el contrato visible en Swagger ni la respuesta real. |

## 5. Estrategia de tests y verificación

### 5.1 Lógica y datos (pytest + pytest-asyncio + httpx)

Crear [`tests/test_personajes_sin_tripulacion.py`](../../tests/test_personajes_sin_tripulacion.py) con `NOMBRE_DB_TEST = "onepiece_test"` a nivel de módulo (el guard `pytest_collection_modifyitems` de [`tests/conftest.py`](../../tests/conftest.py) lo exige) y tests independientes que usan las fixtures `db_test` y `cliente_http` ya existentes.

**Datos de prueba (coherentes con el estilo de [`tests/test_estadisticas.py`](../../tests/test_estadisticas.py)):** documentos con `nombre` y, según el caso, `tripulacion` con un `ObjectId` (reutilizando el patrón `ID_PAJA`, `ID_BARBANEGRA`, `ID_SIN_DOCUMENTO` de `tests/test_estadisticas.py:19-21`), `None`, campo ausente o `""`.

| Test | Descripción | Datos (colección `personajes`) | Resultado esperado | RF cubiertos |
|---|---|---|---|---|
| `test_personajes_sin_tripulacion_coleccion_vacia` | Colección vacía | Sin documentos | `200` + `{"cantidad": 0}` | RF-1, RF-2, RF-5, RF-6 |
| `test_personajes_sin_tripulacion_estructura_solo_cantidad` | Estructura exacta | `{"nombre": "A"}` | `200`, `set(datos.keys()) == {"cantidad"}`, `isinstance(datos["cantidad"], int)` | RF-2, RF-6 |
| `test_personajes_sin_tripulacion_post_no_permitido` | Método POST | Sin datos | `405` | Caso límite (método ≠ GET) |
| `test_personajes_sin_tripulacion_put_no_permitido` | Método PUT | Sin datos | `405` | Caso límite (método ≠ GET) |
| `test_personajes_sin_tripulacion_mezcla` | Mezcla con/sin tripulación | 2 con `tripulacion` (`ObjectId`) + 2 sin (`None` y campo ausente) | `{"cantidad": 2}` | RF-3, RF-4 |
| `test_personajes_sin_tripulacion_campo_ausente_y_null` | Solo ausente y `null` | `{"nombre": "A"}`, `{"nombre": "B", "tripulacion": None}` | `{"cantidad": 2}` | RF-3, RF-4 |
| `test_personajes_sin_tripulacion_objectid_sin_documento_no_cuenta` | `ObjectId` sin documento referenciado | `{"nombre": "A", "tripulacion": ID_SIN_DOCUMENTO}` | `{"cantidad": 0}` | RF-4 |
| `test_personajes_sin_tripulacion_cadena_vacia_cuenta_como_con` | Valor no-`ObjectId` asignado | `{"nombre": "A", "tripulacion": ""}` | `{"cantidad": 0}` | RF-4 |
| `test_personajes_sin_tripulacion_ignora_tripulantes` | Solo cuenta `personajes` | 1 en `personajes` sin tripulación + 2 en `tripulantes` sin tripulación | `{"cantidad": 1}` | RF-7 |
| `test_personajes_sin_tripulacion_todos_con_tripulacion` | Todos con tripulación | 2 con `tripulacion` (`ObjectId`) | `{"cantidad": 0}` | RF-3, RF-4 |
| `test_personajes_sin_tripulacion_unico_sin_tripulacion` | Un único personaje sin tripulación | `{"nombre": "A"}` | `{"cantidad": 1}` | RF-3 |

**Notas de implementación de tests:**
- Insertar vía `await db_test.personajes.insert_many([...])` / `insert_one(...)` (igual que `tests/test_estadisticas.py`); el aislamiento y la limpieza los garantiza la fixture `db_test` de `tests/conftest.py`.
- Verificar el código de estado y comparar el JSON completo (`res.json() == {"cantidad": n}`) además del `set` de claves para asegurar que no hay campos extra.
- Para `""` y para `ObjectId` sin documento, el resultado esperado es `0` (cuentan como con tripulación), según las Definiciones de la spec.
- Los tests de `405` validan que FastAPI responde método no permitido, caso límite de la spec; no requieren datos.

### 5.2 Regresión

No se modifica ningún endpoint existente; los tests actuales de [`tests/test_estadisticas.py`](../../tests/test_estadisticas.py) y [`tests/test_recompensas_resumen.py`](../../tests/test_recompensas_resumen.py) deben seguir pasando sin cambios (criterio de finalización: "Los endpoints existentes no cambian su comportamiento ni su contrato").

### 5.3 Contrato HTTP (solo lectura)

Verificación manual por el usuario (el agente no ejecuta uvicorn ni pytest):

1. **Servidor** (PowerShell, usuario): `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload`
2. **`/docs`**: comprobar que aparece `GET /estadisticas/personajes/sin-tripulacion` con esquema de respuesta de un solo campo `cantidad` (entero).
3. **`GET http://localhost:8000/estadisticas/personajes/sin-tripulacion`**: verificar código `200`, `Content-Type: application/json` y cuerpo `{"cantidad": <entero >= 0>}` con **exactamente** ese campo.

> **Importante:** Chrome DevTools se usa **solo para lectura** (GET y `/docs`), nunca para escribir datos. Los casos con datos conocidos se comprueban únicamente con los tests.

### 5.4 Comando de tests (usuario, PowerShell)

```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v
```

Los tests solo escriben en `onepiece_test`.

## 6. Mapeo RF → implementación/tests

| RF | Descripción | Implementación (`main.py`) | Test(s) |
|---|---|---|---|
| RF-1 | `GET /estadisticas/personajes/sin-tripulacion` → `200`. Métodos distintos de GET → `405` | `@app.get("/estadisticas/personajes/sin-tripulacion", response_model=PersonajesSinTripulacion)` devuelve `200`; FastAPI responde `405` a otros métodos. | `test_personajes_sin_tripulacion_coleccion_vacia`, `test_personajes_sin_tripulacion_post_no_permitido`, `test_personajes_sin_tripulacion_put_no_permitido`, resto (verifican `200`). |
| RF-2 | JSON con exactamente un campo `cantidad` entero y ningún otro | Modelo `PersonajesSinTripulacion` con `extra="forbid"` y el campo `cantidad: int`; se devuelve `{"cantidad": cantidad}`. | `test_personajes_sin_tripulacion_estructura_solo_cantidad`, validación en todos los tests. |
| RF-3 | `cantidad` = nº de documentos de `personajes` sin tripulación asignada | `await db.personajes.count_documents({"tripulacion": None})`. | `test_personajes_sin_tripulacion_mezcla`, `test_personajes_sin_tripulacion_todos_con_tripulacion`, `test_personajes_sin_tripulacion_unico_sin_tripulacion`. |
| RF-4 | Cuenta si `tripulacion` ausente o `null`; no cuenta si tiene cualquier otro valor (incl. `ObjectId` sin documento y `""`) | El filtro `{"tripulacion": None}` coincide solo con ausente/`null`; cualquier otro valor queda fuera. | `test_personajes_sin_tripulacion_mezcla`, `test_personajes_sin_tripulacion_campo_ausente_y_null`, `test_personajes_sin_tripulacion_objectid_sin_documento_no_cuenta`, `test_personajes_sin_tripulacion_cadena_vacia_cuenta_como_con`. |
| RF-5 | Colección `personajes` vacía → `200` y `cantidad` = `0` | `count_documents` devuelve `0` con colección vacía. | `test_personajes_sin_tripulacion_coleccion_vacia`. |
| RF-6 | `cantidad` siempre entero `>= 0` (nunca `null`, negativo ni texto) | El tipo `int` del modelo y el retorno de `count_documents` garantizan un entero `>= 0`. | `test_personajes_sin_tripulacion_estructura_solo_cantidad`, `test_personajes_sin_tripulacion_coleccion_vacia`. |
| RF-7 | El conteo usa solo documentos de `personajes`, sin otras colecciones | Se consulta únicamente `db.personajes`; no se toca `tripulantes` ni tripulaciones. | `test_personajes_sin_tripulacion_ignora_tripulantes`. |

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Confundir "sin tripulación" con "tripulación inexistente" y hacer `$lookup` a tripulaciones | La spec (Definiciones, RF-4) fija que basta mirar el campo `tripulacion`; el diseño usa `{"tripulacion": None}`, sin resolver referencias. Test específico (`objectid_sin_documento_no_cuenta`). |
| Interpretar la cadena vacía `""` como ausente | La spec decide que `""` cuenta como con tripulación; el filtro `{"tripulacion": None}` no la incluye. Test específico (`cadena_vacia_cuenta_como_con`). |
| Contar por error `tripulantes` | Se consulta solo `db.personajes` (RF-7); test específico (`ignora_tripulantes`). |
| Modificar accidentalmente un endpoint existente | Solo se añaden un modelo y un endpoint nuevos; la suite de regresión existente debe seguir en verde. |
| Usar una base distinta de `onepiece_test` | La fixture `db_test` de `tests/conftest.py` fuerza `onepiece_test` y hace `monkeypatch` de `main.db`; el guard aborta si un módulo declara otra base. El nuevo archivo declara `NOMBRE_DB_TEST = "onepiece_test"`. |

## 8. Entregables

- [`main.py`](../../main.py) modificado (modelo `PersonajesSinTripulacion` + endpoint `GET /estadisticas/personajes/sin-tripulacion`).
- [`tests/test_personajes_sin_tripulacion.py`](../../tests/test_personajes_sin_tripulacion.py) creado (11 tests según la tabla de la sección 5.1).
- Este `plan.md` y su `tasks.md`.

## 9. Verificación final (comandos usuario)

**Tests (PowerShell):**
```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v
```

**Contrato HTTP (solo lectura):**
```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Luego revisar `http://localhost:8000/docs` y `http://localhost:8000/estadisticas/personajes/sin-tripulacion` (solo GET/lectura).

El plan cumple los puntos obligatorios de la skill **sdd** y respeta `docs/constitution.md`, `AGENTS.md` y `MEMORY.md`.
