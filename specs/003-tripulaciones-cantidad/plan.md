# Plan: `specs/003-tripulaciones-cantidad/plan.md`

**Spec de referencia:** [`specs/003-tripulaciones-cantidad/spec.md`](./spec.md) – **Estado: aprobada**. 

## 1. Objetivo y alcance

Añadir un nuevo endpoint **de solo lectura** `GET /estadisticas/tripulaciones/cantidad` que devuelva únicamente un JSON con un único campo `cantidad` (entero `>= 0`), igual al número de documentos de la colección de tripulaciones resuelta con el mismo mecanismo que `/estadisticas/tripulaciones` (RF-1–RF-7).

- **Complementa** (no reemplaza ni modifica) a `/estadisticas/tripulaciones` y el resto de endpoints existentes.
- Reutiliza la arquitectura existente: `main.py` (app FastAPI, modelos Pydantic y endpoints), conexión Mongo asíncrona vía Motor.
- El conteo cuenta **documentos de la colección de tripulaciones** (la colección seleccionada entre las colecciones candidatas con el mecanismo compartido con `/estadisticas/tripulaciones`), no miembros; no consulta ni tiene en cuenta `personajes` ni `tripulantes`, ni el campo `numeroMiembros` (RF-3, RF-4).
- Si no existe ninguna colección candidata (`tripulaciones` ni `tripulacions`), responde `200` con `cantidad` = `0` (RF-7).
- Reutiliza el mecanismo de resolución de nombre compartido con `/estadisticas/tripulaciones` (no duplicarlo) - usar el helper `coleccion_tripulaciones(existentes)` ya existente en `main.py`.
- Tests de integración con `pytest + pytest-asyncio + httpx` contra Mongo real, usando **siempre** la base `onepiece_test`.
- Verificación de contrato HTTP vía Chrome DevTools (solo lectura) contra `http://localhost:8000` (`/docs` y la URL del endpoint).

El agente **NO** ejecuta pytest ni arranca uvicorn: los corre el usuario desde PowerShell.

## 2. Archivos a crear/modificar y responsabilidades

| Archivo | Acción | Responsabilidades |
|---|---|---|
| [`main.py`](../../main.py) | **Modificar** | En el bloque de modelos Pydantic añadir un modelo estricto `TripulacionesCantidad(BaseModel)` con `model_config = {"extra": "forbid"}` y un único campo `cantidad: int` (mismo estilo que `PersonajesSinTripulacion` y `RecompensasResumen`). En el bloque de endpoints añadir `@app.get("/estadisticas/tripulaciones/cantidad", response_model=TripulacionesCantidad)`. Reutilizar `db.list_collection_names()` y el helper `coleccion_tripulaciones(existentes)` ya existente para resolver la colección. Si no existe ninguna colección candidata, devolver `{"cantidad": 0}`. Contar documentos con `db[coleccion].count_documents({})`. **No** tocar ningún endpoint existente ni el bloque de helpers de agregación. |
| [`tests/test_tripulaciones_cantidad.py`](../../tests/test_tripulaciones_cantidad.py) | **Crear** | Tests de integración (pytest + pytest-asyncio + httpx) que cubren todos los RF y los casos límite de la spec. Debe declarar `NOMBRE_DB_TEST = "onepiece_test"` a nivel de módulo para pasar el guard de [`tests/conftest.py`](../../tests/conftest.py). Inserta datos directamente en Mongo y llama al endpoint vía la fixture `cliente_http`. **No usan** la base `onepiece`. |

**Archivos que NO se tocan:**
- [`tests/conftest.py`](../../tests/conftest.py): ya expone las fixtures `db_test` y `cliente_http`.
- [`tests/test_estadisticas.py`](../../tests/test_estadisticas.py), [`tests/test_recompensas_resumen.py`](../../tests/test_recompensas_resumen.py), [`tests/test_personajes_sin_tripulacion.py`](../../tests/test_personajes_sin_tripulacion.py): solo se usan como referencia de estilo y como regresión.

**Notas de arquitectura:**
- `main.py` ya contiene `app = FastAPI()`, el cliente Motor y `db = cliente.get_default_database()`, los modelos Pydantic, los endpoints y el helper `coleccion_tripulaciones()`. Se mantiene el estilo existente.
- No se añaden dependencias.
- La ruta nueva es un segmento fijo bajo `/estadisticas/tripulaciones/` (`/estadisticas/tripulaciones/cantidad`), distinto al existente `/estadisticas/tripulaciones`.

## 3. Lógica (algoritmo/pseudocódigo) que cubre todos los RF

### 3.1 Modelo Pydantic de respuesta

```python
class TripulacionesCantidad(BaseModel):
    model_config = {"extra": "forbid"}
    cantidad: int
```
(RF-2, RF-6)

### 3.2 Conteo de tripulaciones

```text
1. existentes = await db.list_collection_names()
2. coleccion = await coleccion_tripulaciones(existentes)  # reutiliza helper existente
3. cantidad = await db[coleccion].count_documents({})
4. return {"cantidad": cantidad}
```

**Nota:** contar documentos en una colección que no existe devuelve 0 sin crearla. Como el helper devuelve un nombre por defecto cuando ninguna candidata existe, ese 0 sale del propio conteo y el test `test_tripulaciones_cantidad_sin_coleccion_candidata` de T3 lo comprueba.

- Usa el mismo mecanismo de resolución que `/estadisticas/tripulaciones` (RF-7). Reutiliza el helper `coleccion_tripulaciones()` sin duplicar lógica.
- Cuenta solo documentos de la colección de tripulaciones resuelta (RF-3, RF-4).
- Si no existe ninguna colección candidata → `200` con `cantidad` = `0` (RF-7).
- Lectura pura: no crea, modifica ni borra nada (RNF-1).

### 3.3 Cobertura de los RF

- RF-1: el endpoint `@app.get(...)` responde `200`.
- RF-2: modelo con `extra="forbid"` y un solo campo `cantidad`.
- RF-3: cuenta documentos de la colección de tripulaciones resuelta.
- RF-4: solo cuenta documentos de la colección de tripulaciones, sin consultar `personajes` ni `tripulantes`.
- RF-5: colección vacía → `count_documents({})` devuelve `0`.
- RF-6: `count_documents` siempre devuelve `int >= 0`.
- RF-7: reutiliza mismo mecanismo que `/estadisticas/tripulaciones`; si no hay ninguna colección candidata → `200` con `cantidad` = `0`.

## 4. Decisiones técnicas justificadas

| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| **Añadir el endpoint en `main.py`** | Proyecto pequeño; mantiene coherencia con endpoints existentes. | Crear módulo/router nuevo: añade complejidad innecesaria. |
| **Modelo `TripulacionesCantidad` con `model_config = {"extra": "forbid"}`** | Garantiza contrato estricto (exactamente campo `cantidad`) y tipo entero, siguiendo estilo existente. | Devolver `dict` sin `response_model`: no valida forma exacta. |
| **Reutilizar `coleccion_tripulaciones(existentes)`** | La spec exige usar el mismo mecanismo que `/estadisticas/tripulaciones` para resolver la colección (RF-7). | Duplicar lógica de resolución: viola la decisión explícita de reutilizarla. |
| **`count_documents({})` sobre la colección resuelta** | Cuenta documentos de tripulaciones directamente; independiente de miembros (RF-4). | Usar `$lookup` o contar desde `personajes`/`tripulantes`: contradice RF-4. |
| **Si no existe ninguna colección candidata → `200` con `cantidad: 0`** | Especificado explícitamente en RF-7 y en decisiones de la spec. | Devolver error: no está en los requisitos. |
| **Tests de integración con datos en Mongo real (`onepiece_test`)** | Sigue patrón existente con fixtures `db_test` y `cliente_http`. | Mocks: no validan comportamiento real. |

## 5. Estrategia de tests y verificación

### 5.1 Lógica y datos (pytest + pytest-asyncio + httpx)

Crear [`tests/test_tripulaciones_cantidad.py`](../../tests/test_tripulaciones_cantidad.py) con `NOMBRE_DB_TEST = "onepiece_test"` a nivel de módulo. Usar fixtures `db_test` y `cliente_http`.

**Datos de prueba:** documentos en colección de tripulaciones (puede ser `tripulaciones` o `tripulacions` según caso). También probar que miembros en `personajes`/`tripulantes` no afectan al conteo.

| Test | Descripción | Datos | Resultado esperado | RF cubiertos |
|---|---|---|---|---|
| `test_tripulaciones_cantidad_coleccion_vacia` | Colección de tripulaciones existe pero vacía | Colección `tripulaciones` sin documentos | `200` + `{"cantidad": 0}` | RF-1, RF-2, RF-5, RF-6 |
| `test_tripulaciones_cantidad_estructura_solo_cantidad` | Estructura exacta | Colección `tripulaciones` con 1 documento `{"nombre": "Sombrero de Paja"}` | `200`, `set(datos.keys()) == {"cantidad"}`, `isinstance(datos["cantidad"], int)`, `datos["cantidad"] == 1` | RF-2, RF-6 |
| `test_tripulaciones_cantidad_post_no_permitido` | Método POST | Sin datos | `405` | Caso límite |
| `test_tripulaciones_cantidad_put_no_permitido` | Método PUT | Sin datos | `405` | Caso límite |
| `test_tripulaciones_cantidad_cuenta_documentos_no_miembros` | Cuenta documentos, no miembros | Colección `tripulaciones` con 3 documentos. Añadir miembros en `personajes`/`tripulantes` apuntando a ellos (o no) | `200` + `{"cantidad": 3}` (independiente de número de miembros) | RF-3, RF-4 |
| `test_tripulaciones_cantidad_sin_coleccion_candidata` | Ninguna colección candidata existe | Borrar/asegurar que ni `tripulaciones` ni `tripulacions` existen | `200` + `{"cantidad": 0}` | RF-7 |
| `test_tripulaciones_cantidad_usa_tripulacions` | Cuenta cuando solo existe `tripulacions` | Crear documentos solo en `tripulacions` | `200` + `{"cantidad": n}` (mismo conteo que usaría `/estadisticas/tripulaciones`) | RF-7 |
| `test_tripulaciones_cantidad_ignora_personajes_tripulantes` | No consulta personajes/tripulantes | Solo colecciones candidatas with documents; many documents in `personajes`/`tripulantes` | Conteo solo de documentos de tripulaciones | RF-4 |
| `test_tripulaciones_cantidad_tripulaciones_sin_miembros` | Tripulaciones sin miembros cuentan | Documentos en `tripulaciones` sin que haya miembros que apunten | `{"cantidad": n}` correcto | RF-3, RF-4, caso límite |
| `test_tripulaciones_cantidad_unica_tripulacion` | Una única tripulación | 1 documento en colección de tripulaciones | `{"cantidad": 1}` | RF-3 |
| `test_tripulaciones_cantidad_existen_ambas_candidatas` | Existen ambas colecciones candidatas a la vez | Datos propios en `onepiece_test`: existen `tripulaciones` y `tripulacions`. Insertar documentos en ambas según corresponda | `200` + `{"cantidad": ...}` igual al conteo que hace `/estadisticas/tripulaciones` (se cuenta la misma colección resuelta) | RF-7 |
| `test_tripulaciones_cantidad_parametro_consulta_ignorado` | Se ignora un parámetro de consulta sin error | Datos propios en `onepiece_test`: petición a `/estadisticas/tripulaciones/cantidad` con algún parámetro de consulta (p.ej. `?x=1`) | `200` + JSON con solo `cantidad`, sin error | RF-1, RF-2 |

**Notas:**
- Debe declarar `NOMBRE_DB_TEST = "onepiece_test"` a nivel de módulo.
- Verificar código de estado y JSON completo.
- Los tests de `405` validan método no permitido.
- Reutilizar patrón de fixtures `db_test`/`cliente_http` como en tests existentes.

### 5.2 Regresión
Los endpoints existentes no deben cambiar; `tests/test_estadisticas.py`, `tests/test_recompensas_resumen.py`, `tests/test_personajes_sin_tripulacion.py` deben seguir pasando.

### 5.3 Contrato HTTP (solo lectura)
1. Servidor (PowerShell, usuario): `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload`
2. `/docs`: comprobar que aparece `GET /estadisticas/tripulaciones/cantidad` con esquema de respuesta con un solo campo `cantidad` (entero).
3. `GET http://localhost:8000/estadisticas/tripulaciones/cantidad`: código `200`, `Content-Type: application/json`, cuerpo `{"cantidad": <entero >= 0>}` con exactamente ese campo.

> Chrome DevTools solo para lectura (GET y `/docs`).

### 5.4 Comando de tests (usuario, PowerShell)
```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v
```
Los tests solo escriben en `onepiece_test`.

## 6. Mapeo RF → implementación/tests

| RF | Descripción | Implementación (`main.py`) | Test(s) |
|---|---|---|---|
| RF-1 | `GET /estadisticas/tripulaciones/cantidad` → `200`. Métodos distintos de GET → `405` | `@app.get("/estadisticas/tripulaciones/cantidad", response_model=TripulacionesCantidad)`. FastAPI responde `405` a otros métodos. | `test_tripulaciones_cantidad_coleccion_vacia`, `test_tripulaciones_cantidad_post_no_permitido`, `test_tripulaciones_cantidad_put_no_permitido`, `test_tripulaciones_cantidad_parametro_consulta_ignorado` |
| RF-2 | JSON con exactamente un campo `cantidad` entero y ningún otro | Modelo `TripulacionesCantidad` con `extra="forbid"`, campo `cantidad: int`. | `test_tripulaciones_cantidad_estructura_solo_cantidad`, `test_tripulaciones_cantidad_parametro_consulta_ignorado` |
| RF-3 | `cantidad` = nº de documentos de la colección de tripulaciones resuelta | `db[coleccion].count_documents({})` sobre colección resuelta. | `test_tripulaciones_cantidad_cuenta_documentos_no_miembros`, `test_tripulaciones_cantidad_unica_tripulacion`, `test_tripulaciones_cantidad_tripulaciones_sin_miembros` |
| RF-4 | Cuenta solo documentos de colección de tripulaciones, sin `personajes`/`tripulantes` | Solo consulta colección resuelta, no usa `personajes`/`tripulantes`. | `test_tripulaciones_cantidad_cuenta_documentos_no_miembros`, `test_tripulaciones_cantidad_ignora_personajes_tripulantes` |
| RF-5 | Colección vacía → `200` y `cantidad` = `0` | `count_documents({})` devuelve `0`. | `test_tripulaciones_cantidad_coleccion_vacia` |
| RF-6 | `cantidad` siempre entero `>= 0` | Tipo `int` del modelo y retorno de `count_documents`. | `test_tripulaciones_cantidad_estructura_solo_cantidad`, `test_tripulaciones_cantidad_coleccion_vacia` |
| RF-7 | Reutiliza mismo mecanismo que `/estadisticas/tripulaciones`; si no hay ninguna colección candidata → `200` con `cantidad` = `0` | Usa `db.list_collection_names()` y `coleccion_tripulaciones(existentes)`. El conteo sobre la colección devuelta por el helper da `0` cuando no hay candidata. | `test_tripulaciones_cantidad_sin_coleccion_candidata`, `test_tripulaciones_cantidad_usa_tripulacions`, `test_tripulaciones_cantidad_existen_ambas_candidatas` |

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Duplicar lógica de resolución en lugar de reutilizar helper | Usar explícitamente `coleccion_tripulaciones(existentes)` ya existente en `main.py`. |
| Contar miembros en lugar de documentos de tripulaciones | Usar `count_documents({})` sobre la colección resuelta, sin hacer agregaciones sobre `personajes`/`tripulantes`. Test específico. |
| No manejar el caso sin colecciones candidatas | Ese caso queda cubierto por el propio conteo; el test `test_tripulaciones_cantidad_sin_coleccion_candidata` de T3 lo comprueba. |
| Confundir con endpoint existente `/estadisticas/tripulaciones` | Ruta distinta (`/cantidad` al final), sin modificar endpoint existente. |
| Usar base distinta de `onepiece_test` | Declarar `NOMBRE_DB_TEST = "onepiece_test"` en test file y usar fixtures existentes. |

## 8. Pendientes / Preguntas (resueltas)

- (a) Contar en una colección inexistente no la crea, porque contar solo lee.
- (b) Tripulaciones sin campo nombre: el endpoint nuevo cuenta documentos y no lee ese campo.
- (c) Base caída o colección inaccesible: sin manejo especial de errores, como en los demás endpoints (comprobado en main.py: ningún endpoint captura excepciones de la base). No se prueba porque la constitución exige Mongo real.

## 9. Entregables

- [`main.py`](../../main.py) modificado (modelo `TripulacionesCantidad` + endpoint `GET /estadisticas/tripulaciones/cantidad`).
- [`tests/test_tripulaciones_cantidad.py`](../../tests/test_tripulaciones_cantidad.py) creado.
- Este `plan.md` y su `tasks.md`.

## 10. Verificación final (comandos usuario)

**Tests (PowerShell):**
```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v
```

**Contrato HTTP (solo lectura):**
```powershell
$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Luego revisar `http://localhost:8000/docs` y `http://localhost:8000/estadisticas/tripulaciones/cantidad` (solo GET/lectura).

El plan cumple los puntos obligatorios de la skill **sdd** y respeta `docs/constitution.md`, `AGENTS.md` y `MEMORY.md`.
