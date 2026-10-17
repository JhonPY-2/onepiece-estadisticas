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
