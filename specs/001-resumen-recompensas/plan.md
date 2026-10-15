# Plan: `specs/001-resumen-recompensas/plan.md`

**Spec de referencia:** [`specs/001-resumen-recompensas/spec.md`](./spec.md) – **Estado: aprobada**. No existen entradas con `[NECESITA ACLARACIÓN]`.

## 1. Objetivo y alcance

Añadir un nuevo endpoint **de solo lectura** `GET /estadisticas/recompensas/resumen` que devuelva un resumen global de recompensas de los personajes con los seis campos exactos: `cantidad_personajes`, `total_recompensas`, `promedio_recompensa`, `recompensa_maxima`, `recompensa_minima`, `personajes_sin_recompensa`.

- **Complementa** (no reemplaza) a `/estadisticas/resumen`.
- Reutiliza la arquitectura existente: `main.py` (app FastAPI, modelos Pydantic, endpoints), conexión Mongo asíncrona vía `Motor`, colección `personajes`.
- Tests de integración con `pytest + pytest-asyncio + httpx` contra Mongo real, usando **siempre** la base `onepiece_test`.
- Verificación de contrato HTTP vía **MCP de Chrome DevTools** (solo lectura) contra `http://localhost:8000` (docs y URL del endpoint).

El agente **NO** ejecuta pytest ni arranca uvicorn: el usuario los corre desde PowerShell.

## 2. Archivos a crear/modificar y responsabilidades

| Archivo | Acción | Responsabilidades |
|---|---|---|
| [`main.py`](../../main.py) | **Modificar** | Definir modelos Pydantic de respuesta (respuesta estricta con exactamente 6 campos). Añadir endpoint `GET /estadisticas/recompensas/resumen`. Reutilizar `db` existente, colección `personajes` (`db.personajes`). Aplicar reglas de normalización de `recompensa`: campo ausente o `null` → `0`; convertir a entero con redondeo `.5` hacia arriba **antes de agregar** (para total/máx/mín). Contar `personajes_sin_recompensa` como los personajes cuya recompensa ya normalizada vale `0` (incluye ausente, `null`, `0` y valores que redondean a `0`). Calcular promedio con **aritmética entera** (sin `float`/`Decimal`) con redondeo `.5` hacia arriba. Garantizar respuesta determinista y de solo lectura (sin escrituras). No modificar `/estadisticas/resumen`. |
| [`tests/conftest.py`](../../tests/conftest.py) | **Modificar** | Hoy solo contiene el guard `pytest_collection_modifyitems` (aborta si un test no apunta a `onepiece_test`). Se **mueven** aquí las fixtures `db_test` y `cliente_http` (y la constante `NOMBRE_DB_TEST`) que actualmente viven en `tests/test_estadisticas.py`, sin cambiar su comportamiento, para que cualquier archivo de `tests/` las use. `db_test` asegura el aislamiento: conecta a `MONGODB_URI`, verifica `db.name != main.db.name`, hace monkeypatch de `main.db`, limpia la base `onepiece_test` tras cada test; `cliente_http` usa `httpx.ASGITransport`. `tests/test_estadisticas.py` debe seguir pasando. |
| [`tests/test_recompensas_resumen.py`](../../tests/test_recompensas_resumen.py) | **Crear** | Tests de integración (pytest + pytest-asyncio + httpx) que cubren todos los RF y casos límite de la spec. Insertan datos directamente en Mongo (colección `personajes`), llaman al endpoint vía `TestClient`/ASGI, validan código 200, estructura JSON exacta (solo 6 campos, nombres exactos, valores enteros) y valores calculados. Verifican colección vacía (RF-8), personajes sin recompensas (RF-3–RF-7, RF-10), `recompensa` `0`/`null`/ausente, mezcla `0`/`null`/ausente/`0.4` (`personajes_sin_recompensa`), valores no enteros con `.5`, promedio `.5` hacia arriba, caso un solo personaje. **No usan** base `onepiece`. |

**Notas de arquitectura:**
- `main.py` contiene `app = FastAPI()`, conexión Mongo, modelos Pydantic existentes para otros endpoints y lógica de agregación. Se mantiene el estilo y convenciones existentes.
- No se añaden dependencias (usa `pymongo`/Motor ya presente). No hay lint/build.

## 3. Lógica (algoritmo/pseudocódigo) que cubre todos los RF

### 3.1 Modelo Pydantic de respuesta

Definir un modelo estricto para el response (asegura nombres exactos, tipos numéricos enteros y sin campos extra):

```python
from pydantic import BaseModel, ConfigDict

class RecompensasResumen(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cantidad_personajes: int
    total_recompensas: int
    promedio_recompensa: int
    recompensa_maxima: int
    recompensa_minima: int
    personajes_sin_recompensa: int
```

(RF-2, RF-9, RF-10)

### 3.2 Normalización de una recompensa (`recompensa`)

Definir una única función clara para normalizar la recompensa de cada personaje:

```python
import math

def normalizar_recompensa(valor):
    if valor is None:
        return 0
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float):
        return math.floor(valor + 0.5)
    try:
        v = float(valor)
        if v.is_integer():
            return int(v)
        return math.floor(v + 0.5)
    except Exception:
        return 0
```

**Reglas aplicadas:**
- `None` o ausente → `0`.
- `int` → se devuelve tal cual.
- `float` (u otro valor numérico con parte fraccionaria) → `math.floor(v + 0.5)` (redondeo al entero más cercano con regla `.5` hacia arriba).
- Las recompensas son >= 0 por dominio.

**Ejemplos de verificación:**
- `None` → `0`
- `1000` → `1000`
- `1.5` → `2`
- `2.4` → `2`
- `1500.7` → `1501`

Esta función se aplica a cada documento para obtener `r_norm` usado en `total`, `max` y `min` (RF-4, RF-6, RF-7).

### 3.3 Inicialización de valores

Para el recorrido de documentos: se inicializan `total = 0`, `max_r = None`, `min_r = None` y `sin_recompensa = 0`. Tras obtener el primer valor `r_norm`, `max_r` y `min_r` se inicializan con ese valor para simplificar.

### 3.4 Agregación en endpoint

Endpoint: `GET /estadisticas/recompensas/resumen` (RF-1)

Lógica (se realiza **una sola lectura** de la colección `personajes`, contando los documentos dentro del mismo recorrido del cursor):

```text
1. Obtener colección `personajes`: `col = db.personajes`
2. Inicializar: contador = 0, total = 0, max_r = None, min_r = None, sin_recompensa = 0
3. Iterar todos los documentos con cursor (async), proyectando solo `recompensa`:
     `async for doc in col.find({}, {"recompensa": 1}):`
       - contador += 1
       - r = normalizar_recompensa(doc.get("recompensa"))
       - total += r
       - if r == 0: sin_recompensa += 1
       - if max_r is None or r > max_r: max_r = r
       - if min_r is None or r < min_r: min_r = r
4. Si `contador == 0`:
     → respuesta {cantidad_personajes:0, total_recompensas:0, promedio_recompensa:0, recompensa_maxima:0, recompensa_minima:0, personajes_sin_recompensa:0}
5. Si `contador > 0`:
     - calcular promedio = promedio_recompensas(total, contador) (RF-5)
     - respuesta con enteros: cantidad_personajes=contador, total_recompensas=total, promedio_recompensa=promedio, recompensa_maxima=max_r, recompensa_minima=min_r, personajes_sin_recompensa=sin_recompensa
6. Retornar 200 + JSON (RF-1, RF-2, RF-9, RF-10)
```

El contador `sin_recompensa` se incrementa en el **mismo recorrido** del cursor (no se hace una segunda consulta) y cuenta los personajes cuya recompensa normalizada vale `0`: sin campo, `null`, `0` y valores que redondean a `0` (p. ej. `0.4`) (RF-10).

No se utiliza `count_documents` por separado: el recuento de personajes se obtiene dentro del mismo recorrido, lo que reduce lecturas y cumple el requisito de una sola lectura cuando hay datos.

### 3.5 Cálculo de promedio con aritmética entera (RF-5)

Función única y clara para calcular el promedio:

```text
def promedio_recompensas(total: int, cantidad: int) -> int:
    if cantidad == 0:
        return 0
    return (total + cantidad // 2) // cantidad
```

**Reglas aplicadas:**
- Si `cantidad == 0` → `0`.
- En caso contrario → `(total + cantidad // 2) // cantidad` (redondeo al entero más cercano con regla `.5` hacia arriba).
- Cálculo realizado con **aritmética entera** (sin `float` ni `Decimal`).
- Recompensas >= 0.

**Ejemplos de verificación:**
- `(3, 2)` → `(3 + 1) // 2 = 4 // 2 = 2` (1.5 → 2)
- `(2, 2)` → `(2 + 1) // 2 = 1` (1.0 → 1)
- `(5, 2)` → `(5 + 1) // 2 = 6 // 2 = 3` (2.5 → 3)
- `(0, 3)` → `(0 + 1) // 3 = 1 // 3 = 0` (0.0 → 0)
- `(4, 3)` → `(4 + 1) // 3 = 5 // 3 = 1` (1.33… → 1)

Esto cumple RF-5.

### 3.6 Casos borde (todos cubiertos)

- Vacío: contador==0 → devolver seis ceros (RF-8).
- Sin recompensas (todos 0/null/ausente): total 0, max 0, min 0, avg 0, `personajes_sin_recompensa == contador` (RF-3–RF-7, RF-10).
- Mezcla `0`/`null`/ausente/`0.4`: los cuatro cuentan en `personajes_sin_recompensa` (RF-10).
- `recompensa: 0` participa (min puede ser 0).
- `null`/ausente → 0.
- No entero `.5` → half up antes de agregar.
- Un solo personaje: avg = su r_norm.
- Min puede ser 0.

## 4. Decisiones técnicas justificadas

| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| **Añadir endpoint en `main.py`** (no crear módulo nuevo) | Proyecto pequeño (microservicio único). Mantiene coherencia con endpoints existentes (`/estadisticas/*`). Reduce complejidad de imports. | Crear `routers/recompensas.py` y registrar router: añade estructura innecesaria para un único endpoint. |
| **Usar modelo Pydantic `RecompensasResumen` con `extra="forbid"`** | Garantiza contrato estricto: **solo** los 6 campos exactos (RF-2, RF-9). Evita fugas de campos no deseados. | Devolver `dict` sin validación: riesgo de añadir campos accidentalmente, menos explícito. |
| **Leer colección con cursor `find({}, {"recompensa":1})` en un único recorrido, contando dentro del bucle** | Se obtiene `cantidad_personajes`, `total`, `max`, `min` y `personajes_sin_recompensa` en **una sola lectura** de los documentos. Sencillo, claro y eficiente. No requiere `count_documents` aparte. Si el contador queda en 0, se devuelve la respuesta con seis ceros. | Usar `$group` con `$sum`, `$max`, `$min`, `$avg` (Mongo). `$avg` hace redondeo flotante y no garantiza “aritmética entera + .5 hacia arriba” tal como pide RF-5. Además hay que normalizar `null/ausente` (usar `$ifNull`/`$cond`) antes de agregar. Más complejo para cumplir regla exacta de promedio. También usar `count_documents` + recorrido: dos operaciones cuando hay datos. |
| **Calcular promedio con fórmula entera `(total + cantidad // 2) // cantidad`** | Cumple RF-5 explícitamente (**sin `float` ni `Decimal`**) y regla `.5` hacia arriba. Determinista. | Usar `math.floor(total/count + 0.5)` (usa float) o `statistics.mean`/float: contradice RF-5. |
| **Normalización centralizada con `math.floor(v + 0.5)` para valores no enteros** | Implementa exactamente la regla indicada (redondeo al entero más cercano, `.5` hacia arriba), cubre `int`, `float`, valores ausentes o `None`, y es clara y determinista para recompensas >= 0. | Duplicar lógica inline o usar otras estrategias de redondeo. |
| **Tests de integración con httpx.ASGITransport + datos en Mongo real** | Siguen el patrón existente, movido a `tests/conftest.py` (usa DB real `onepiece_test`, monkeypatch de `main.db`). Reflejan comportamiento real con Motor. | Mockear DB: no valida interacción real con colección ni aislamiento. |
| **Contrato HTTP vía MCP Chrome DevTools (solo lectura)** | Cumple requisito obligatorio del plan: verificar ruta, método, código 200, estructura JSON en `/docs` y URL del endpoint contra `http://localhost:8000`. Solo lectura. | Solo tests unitarios: no validan contrato HTTP visible (FastAPI docs/response real). |

## 5. Estrategia de tests y verificación

### 5.1 Lógica y datos (pytest + pytest-asyncio + httpx)

Crear `tests/test_recompensas_resumen.py` con tests independientes. Usar las fixtures `db_test` y `cliente_http` (movidas a `tests/conftest.py` desde `tests/test_estadisticas.py`). Conexión Mongo gestionada por `conftest.py` (limpieza tras test).

**Datos de prueba (coherentes con estilo existente):** documentos con campos mínimos (`_id`, `nombre`, `recompensa` según caso). Usar ObjectId no necesario para estos tests.

| Test | Descripción | Datos (colección `personajes`) | Resultado esperado | RF cubiertos |
|---|---|---|---|---|
| `test_recompensas_resumen_vacio` | Colección vacía | Sin documentos | `{"cantidad_personajes":0,"total_recompensas":0,"promedio_recompensa":0,"recompensa_maxima":0,"recompensa_minima":0,"personajes_sin_recompensa":0}` (200) | RF-1,RF-2,RF-8,RF-9,RF-10 |
| `test_recompensas_sin_recompensas_todos_cero` | Personajes sin `recompensa` (ausente/null) | `{nombre:"A"}`, `{nombre:"B", recompensa:null}`, `{nombre:"C"}` (3) | cantidad 3, total 0, promedio 0, max 0, min 0, `personajes_sin_recompensa` 3 (= cantidad) | RF-3,RF-4,RF-5,RF-6,RF-7,RF-9,RF-10 |
| `test_recompensas_mezcla_cero_null_ausente_y_0_4` | Mezcla de recompensas que normalizan a `0` | `{nombre:"A", recompensa:0}`, `{nombre:"B", recompensa:null}`, `{nombre:"C"}`, `{nombre:"D", recompensa:0.4}`, `{nombre:"E", recompensa:1000}` (5) | cantidad 5, total 1000, promedio 200, max 1000, min 0, `personajes_sin_recompensa` 4 | RF-3,RF-4,RF-5,RF-6,RF-7,RF-10 |
| `test_recompensas_con_cero` | Incluye `recompensa: 0` | `{nombre:"A", recompensa:0}`, `{nombre:"B", recompensa:1000}` | cantidad 2, total 1000, promedio 500, max 1000, min 0, `personajes_sin_recompensa` 1 | RF-3,RF-4,RF-5,RF-6,RF-7,RF-9,RF-10 |
| `test_recompensas_enteras` | Valores enteros positivos | `{nombre:"L", recompensa:3000000000}`, `{nombre:"Z", recompensa:1000000000}` (Luffy mayor) | total 4_000_000_000, promedio 2_000_000_000, max 3e9, min 1e9 | RF-4,RF-5,RF-6,RF-7 |
| `test_recompensas_redondeo_medio_arriba_agregado` | No entero `.5` se redondea **antes de agregar** | `{nombre:"A", recompensa:1.5}`, `{nombre:"B", recompensa:2.4}` → 2 y 2 → total 4, avg 2, max 2, min 2 | Verifica regla half-up previo a suma | RF-4,RF-6,RF-7 |
| `test_recompensas_promedio_medio_arriba` | Promedio fracción `.5` → **hacia arriba** | `{nombre:"A", recompensa:1}`, `{nombre:"B", recompensa:2}` (total 3, count 2 → 1.5 → 2) | promedio 2 | RF-5 |
| `test_recompensas_promedio_medio_arriba_otro` | Otro caso `.5` | `{nombre:"A", recompensa:0}`, `{nombre:"B", recompensa:5}` (2.5→3) | promedio 3 | RF-5 |
| `test_recompensas_unico_personaje` | Un solo documento | `{nombre:"Solo", recompensa:1500.7}` → redondea 1501 | cantidad 1, total 1501, promedio 1501, max 1501, min 1501 | RF-3–RF-7 |
| `test_recompensas_minimo_puede_ser_cero` | Mínimo 0 (ausente + valores) | `{nombre:"X"}`, `{nombre:"Y", recompensa:500}` | min 0, max 500, `personajes_sin_recompensa` 1 | RF-7,RF-10 |
| `test_recompensas_estructura_solo_seis_campos` | Estructura exacta, sin otros campos | Datos mínimos | Claves exactamente: cantidad_personajes,total_recompensas,promedio_recompensa,recompensa_maxima,recompensa_minima,personajes_sin_recompensa. No extra. | RF-2,RF-9,RF-10 |
| `test_recompensas_no_modifica_resumen_existente` | **Regresión**: `/estadisticas/resumen` no cambia | Datos de prueba | Endpoint `/estadisticas/resumen` sigue respondiendo igual que antes (200, estructura propia). No se modifica. | Criterios de finalización de la spec |
| `test_recompensas_metodo_post_devuelve_405` | Método POST no permitido | Datos mínimos (o vacío) | `POST /estadisticas/recompensas/resumen` → `405 Method Not Allowed` | RF-1 (caso límite método distinto de GET) |
| `test_recompensas_metodo_put_devuelve_405` | Método PUT no permitido | Datos mínimos (o vacío) | `PUT /estadisticas/recompensas/resumen` → `405 Method Not Allowed` | RF-1 (caso límite método distinto de GET) |

**Notas de implementación tests:**
- **Actualizar los tests existentes** que comparan exactamente las claves del JSON (p. ej. la comprobación de estructura exacta) para que exijan **seis** campos e incluyan `personajes_sin_recompensa` (RF-2, RF-9, RF-10).
- Usar `httpx.ASGITransport(app=main.app)` + `AsyncClient` o `TestClient` según patrón existente.
- Insertar vía `await main.db.personajes.insert_many([...])` o `insert_one`.
- Limpiar colección entre tests (conftest lo hace). No tocar otras colecciones.
- Verificar tipos: valores enteros (`int` en JSON).
- Los tests de métodos no GET validan que el framework responde `405 Method Not Allowed` (caso límite de la spec).

### 5.2 Contrato HTTP con MCP de Chrome DevTools (solo lectura)

Verificación manual por usuario (agente no ejecuta uvicorn/pytest): 

1. **Levantar servidor** (PowerShell, usuario):  
   `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload`
2. **Abrir Swagger UI**: `http://localhost:8000/docs` (solo lectura GET). Comprobar que aparece nuevo endpoint `GET /estadisticas/recompensas/resumen` con esquema de respuesta `RecompensasResumen` (6 campos).
3. **Probar endpoint**: `http://localhost:8000/estadisticas/recompensas/resumen` con método `GET`. Verificar:
   - Código HTTP `200 OK`
   - `Content-Type: application/json`
   - Cuerpo JSON con exactamente 6 campos, nombres exactos, valores numéricos (enteros)

> **Importante:** Chrome DevTools MCP se usa **solo para lectura** (GET y `/docs`), nunca para escribir datos. Los casos con datos conocidos se verifican únicamente con los tests.

### 5.3 Comando de tests (usuario, PowerShell)

```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v
```

Debe pasar todos los tests (incluyendo los nuevos). Los tests solo escriben en `onepiece_test`.

## 6. Mapeo RF → implementación/tests

| RF | Descripción | Implementación (main.py) | Test(s) |
|---|---|---|---|
| RF-1 | `GET /estadisticas/recompensas/resumen` → `200`. Métodos distintos de GET → `405 Method Not Allowed` | Definir endpoint con `@app.get("/estadisticas/recompensas/resumen")`, devolver modelo Pydantic con status 200 implícito. FastAPI gestiona métodos no permitidos devolviendo 405. | `test_recompensas_resumen_vacio`, `test_recompensas_metodo_post_devuelve_405`, `test_recompensas_metodo_put_devuelve_405`, resto de tests (verifican 200). |
| RF-2 | JSON con 6 campos exactos, solo esos, numéricos; `recompensa_maxima` solo número (sin nombre) | Modelo `RecompensasResumen` con `extra="forbid"`. Campos: `cantidad_personajes`, `total_recompensas`, `promedio_recompensa`, `recompensa_maxima`, `recompensa_minima`, `personajes_sin_recompensa`. Devolver instancia. | `test_recompensas_estructura_solo_seis_campos`, validación en todos tests. |
| RF-3 | `cantidad_personajes` = total documentos `personajes` | Contador obtenido en el mismo recorrido del cursor (`contador += 1`). | `test_recompensas_sin_recompensas_todos_cero`, `test_recompensas_unico_personaje`, etc. |
| RF-4 | `total_recompensas` = suma de recompensas convertidas a entero, contar `0` si ausente/null | Iterar cursor en única lectura, aplicar `normalizar_recompensa` (half-up con `math.floor(v+0.5)`) → acumular `total += r`. | `test_recompensas_enteras`, `test_recompensas_redondeo_medio_arriba_agregado`, casos con 0/null. |
| RF-5 | `promedio_recompensa` = `total/count`, round half up con aritmética entera, `.5` → arriba | `promedio_recompensas(total, cantidad) = 0` si `cantidad==0`, else `(total + cantidad // 2) // cantidad`. | `test_recompensas_promedio_medio_arriba`, `test_recompensas_promedio_medio_arriba_otro`, `test_recompensas_enteras`. |
| RF-6 | `recompensa_maxima` = mayor entre todas, tratar 0 si ausente/null | `max_r` actualizado en el mismo recorrido con `normalizar_recompensa`. | `test_recompensas_con_cero`, `test_recompensas_minimo_puede_ser_cero`, `test_recompensas_enteras`. |
| RF-7 | `recompensa_minima` = menor entre todas, puede ser 0 | `min_r` actualizado en el mismo recorrido con `normalizar_recompensa`. | `test_recompensas_minimo_puede_ser_cero`, `test_recompensas_con_cero`. |
| RF-8 | Colección vacía → seis campos 0, HTTP 200 | Si `contador == 0` tras recorrido: devolver seis ceros. | `test_recompensas_resumen_vacio`. |
| RF-9 | Siempre 6 campos con nombres exactos, valores numéricos enteros | Modelo Pydantic + respuesta directa. Usar `int` (Python) → JSON números enteros. | Todos tests. |
| RF-10 | `personajes_sin_recompensa` = nº de personajes sin `recompensa`, con `null` o cuya recompensa normalizada vale `0` | En el mismo recorrido del cursor: `if r == 0: sin_recompensa += 1`. Sin segunda consulta. | `test_recompensas_sin_recompensas_todos_cero`, `test_recompensas_mezcla_cero_null_ausente_y_0_4`, `test_recompensas_con_cero`, `test_recompensas_resumen_vacio`. |

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Precisión de redondeo (`.5`): confundir round half up vs banker's rounding | Usar `math.floor(v + 0.5)` para normalización y fórmula entera `(total + cantidad // 2) // cantidad` para promedio, con tests específicos para `.5` (agregado y promedio). |
| Trabajar con `float`/`double` de Mongo para no enteros | Aplicar normalización explícita (detección de `int`/`float` y `math.floor(v + 0.5)`). Tests con `1.5`, `2.4`, `1500.7`. |
| Modificar accidentalmente `/estadisticas/resumen` | Solo añadir nuevo endpoint y tests de regresión `test_recompensas_no_modifica_resumen_existente`. |
| No usar base correcta en tests | `conftest.py` centraliza el aislamiento: la fixture `db_test` (movida desde `tests/test_estadisticas.py`) garantiza `onepiece_test` y hace monkeypatch de `main.db`; el guard `pytest_collection_modifyitems` sigue abortando si un test apunta a otra base. Los tests no configuran URI propia. |

## 8. Entregables

- [`main.py`](../../main.py) modificado (nuevo endpoint + modelos).
- [`tests/test_recompensas_resumen.py`](../../tests/test_recompensas_resumen.py) creado (14 tests según tabla).
- [`tests/conftest.py`](../../tests/conftest.py) modificado (mueve `NOMBRE_DB_TEST`, `db_test` y `cliente_http` desde `tests/test_estadisticas.py` para compartirlas entre tests).
- Plan [`specs/001-resumen-recompensas/plan.md`](./plan.md) actualizado (este archivo).

## 9. Verificación final (comandos usuario)

**Tests (PowerShell):**
```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v
```

**Contrato HTTP (opcional lectura):**
```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Luego revisar `http://localhost:8000/docs` y `http://localhost:8000/estadisticas/recompensas/resumen` con Chrome DevTools MCP (solo GET/lectura).

El plan cumple todos los puntos obligatorios del skill **sdd** y sigue las convenciones de AGENTS.md.