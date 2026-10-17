# tests/test_personajes_sin_tripulacion.py
"""Tests del endpoint GET /estadisticas/personajes/sin-tripulacion (RF-1, RF-2, RF-5, RF-6)."""

NOMBRE_DB_TEST = "onepiece_test"  # requerido por el guard de tests/conftest.py


async def test_personajes_sin_tripulacion_coleccion_vacia(cliente_http):
    """RF-5: colección vacía → 200 y cantidad == 0."""
    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 0}


async def test_personajes_sin_tripulacion_estructura_solo_cantidad(cliente_http, db_test):
    """RF-2: el JSON tiene exactamente un campo 'cantidad' de tipo int."""
    await db_test.personajes.insert_one({"nombre": "A"})

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    datos = res.json()
    assert set(datos.keys()) == {"cantidad"}
    assert isinstance(datos["cantidad"], int)


async def test_personajes_sin_tripulacion_post_no_permitido(cliente_http):
    """RNF-1: el endpoint es de solo lectura; POST → 405."""
    res = await cliente_http.post("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 405


async def test_personajes_sin_tripulacion_put_no_permitido(cliente_http):
    """RNF-1: el endpoint es de solo lectura; PUT → 405."""
    res = await cliente_http.put("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 405


# --- T3: tests de conteo y casos límite (RF-3, RF-4, RF-7) ---
# El import va aquí, al inicio del bloque añadido, para no alterar ninguna
# línea de los 4 tests de T1 que ya están verificados.

from bson import ObjectId

# Mismos ObjectId del patrón real de tests/test_estadisticas.py:19-21.
_ID_PAJA = ObjectId("6ab49840bf5269d5b9e9afa8")
_ID_BARBANEGRA = ObjectId("6ab34fb62f4472871fb4a62e")
_ID_SIN_DOCUMENTO = ObjectId("000000000000000000000001")


async def test_personajes_sin_tripulacion_mezcla(cliente_http, db_test):
    """RF-3, RF-4: 2 con tripulación (ObjectId) + 2 sin (None y ausente) → 2."""
    await db_test.personajes.insert_many([
        {"nombre": "A", "tripulacion": _ID_PAJA},
        {"nombre": "B", "tripulacion": _ID_BARBANEGRA},
        {"nombre": "C", "tripulacion": None},
        {"nombre": "D"},
    ])

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 2}


async def test_personajes_sin_tripulacion_campo_ausente_y_null(cliente_http, db_test):
    """RF-4: campo ausente y campo null se cuentan los dos → 2."""
    await db_test.personajes.insert_many([
        {"nombre": "A"},
        {"nombre": "B", "tripulacion": None},
    ])

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 2}


async def test_personajes_sin_tripulacion_objectid_sin_documento_no_cuenta(cliente_http, db_test):
    """RF-4: ObjectId sin documento en tripulaciones cuenta como con → 0."""
    # No se crea ningún documento en la colección de tripulaciones: la
    # asignación existe en el propio personaje, así que no entra en la cantidad.
    await db_test.personajes.insert_one({"nombre": "A", "tripulacion": _ID_SIN_DOCUMENTO})

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 0}


async def test_personajes_sin_tripulacion_cadena_vacia_cuenta_como_con(cliente_http, db_test):
    """RF-4: cadena vacía es valor asignado, cuenta como con tripulación → 0."""
    await db_test.personajes.insert_one({"nombre": "A", "tripulacion": ""})

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 0}


async def test_personajes_sin_tripulacion_ignora_tripulantes(cliente_http, db_test):
    """RF-7: solo cuenta la colección personajes; tripulantes queda fuera → 1."""
    await db_test.personajes.insert_one({"nombre": "A"})
    await db_test.tripulantes.insert_many([
        {"nombre": "B"},
        {"nombre": "C"},
    ])

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 1}


async def test_personajes_sin_tripulacion_todos_con_tripulacion(cliente_http, db_test):
    """RF-3, RF-4: los 2 personajes tienen ObjectId → 0."""
    await db_test.personajes.insert_many([
        {"nombre": "A", "tripulacion": _ID_PAJA},
        {"nombre": "B", "tripulacion": _ID_BARBANEGRA},
    ])

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 0}


async def test_personajes_sin_tripulacion_unico_sin_tripulacion(cliente_http, db_test):
    """RF-3: un único documento en personajes y sin tripulación → 1."""
    await db_test.personajes.insert_one({"nombre": "A"})

    res = await cliente_http.get("/estadisticas/personajes/sin-tripulacion")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 1}
