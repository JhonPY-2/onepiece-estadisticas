# tests/test_tripulaciones_cantidad.py
"""Tests del endpoint GET /estadisticas/tripulaciones/cantidad (RF-1, RF-2, RF-5, RF-6)."""

NOMBRE_DB_TEST = "onepiece_test"  # requerido por el guard de tests/conftest.py


async def test_tripulaciones_cantidad_coleccion_vacia(cliente_http):
    """RF-5: colección tripulaciones vacía → 200 y cantidad == 0."""
    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 0}


async def test_tripulaciones_cantidad_estructura_solo_cantidad(cliente_http, db_test):
    """RF-2: el JSON tiene exactamente un campo 'cantidad' de tipo int."""
    await db_test.tripulaciones.insert_one({"nombre": "Sombrero de Paja"})

    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    datos = res.json()
    assert set(datos.keys()) == {"cantidad"}
    assert isinstance(datos["cantidad"], int)


async def test_tripulaciones_cantidad_post_no_permitido(cliente_http):
    """RNF-1: el endpoint es de solo lectura; POST → 405."""
    res = await cliente_http.post("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 405


async def test_tripulaciones_cantidad_put_no_permitido(cliente_http):
    """RNF-1: el endpoint es de solo lectura; PUT → 405."""
    res = await cliente_http.put("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 405


async def test_tripulaciones_cantidad_cuenta_documentos_no_miembros(cliente_http, db_test):
    """RF-3, RF-4: cuenta documentos de tripulaciones, no los miembros que las referencian."""
    from bson import ObjectId

    id_piratas_a = ObjectId()
    id_piratas_b = ObjectId()
    id_piratas_c = ObjectId()
    await db_test.tripulaciones.insert_many(
        [
            {"_id": id_piratas_a, "nombre": "Piratas A"},
            {"_id": id_piratas_b, "nombre": "Piratas B"},
            {"_id": id_piratas_c, "nombre": "Piratas C"},
        ]
    )
    await db_test.personajes.insert_many(
        [
            {"nombre": "Miembro 1", "recompensa": 100, "tripulacion": id_piratas_a},
            {"nombre": "Miembro 2", "recompensa": 200, "tripulacion": id_piratas_a},
            {"nombre": "Miembro 3", "recompensa": 300, "tripulacion": id_piratas_b},
        ]
    )
    await db_test.tripulantes.insert_many(
        [
            {"nombre": "Miembro 4", "tripulacion": id_piratas_b},
            {"nombre": "Miembro 5", "tripulacion": id_piratas_c},
        ]
    )

    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 3}


async def test_tripulaciones_cantidad_sin_coleccion_candidata(cliente_http):
    """RF-7: sin 'tripulaciones' ni 'tripulacions' → 200 y cantidad == 0."""
    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 0}


async def test_tripulaciones_cantidad_usa_tripulacions(cliente_http, db_test):
    """RF-7: si solo existe 'tripulacions', se cuentan sus documentos."""
    await db_test.tripulacions.insert_many(
        [
            {"nombre": "Piratas A"},
            {"nombre": "Piratas B"},
        ]
    )

    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 2}


async def test_tripulaciones_cantidad_ignora_personajes_tripulantes(cliente_http, db_test):
    """RF-4: los documentos de personajes/tripulantes no suman al conteo."""
    await db_test.tripulaciones.insert_many(
        [
            {"nombre": "Piratas A"},
            {"nombre": "Piratas B"},
        ]
    )
    await db_test.personajes.insert_many(
        [{"nombre": f"Personaje {i}", "recompensa": i} for i in range(5)]
    )
    await db_test.tripulantes.insert_many(
        [{"nombre": f"Tripulante {i}"} for i in range(4)]
    )

    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 2}


async def test_tripulaciones_cantidad_tripulaciones_sin_miembros(cliente_http, db_test):
    """RF-3, RF-4: las tripulaciones sin miembros también cuentan."""
    await db_test.tripulaciones.insert_many(
        [
            {"nombre": "Piratas A", "capitan": "A"},
            {"nombre": "Piratas B", "capitan": "B"},
            {"nombre": "Piratas C", "capitan": "C"},
        ]
    )

    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 3}


async def test_tripulaciones_cantidad_unica_tripulacion(cliente_http, db_test):
    """RF-3: una sola tripulación → cantidad == 1."""
    await db_test.tripulaciones.insert_one({"nombre": "Piratas A"})

    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 1}


async def test_tripulaciones_cantidad_existen_ambas_candidatas(cliente_http, db_test):
    """RF-7: con ambas candidatas se cuenta la misma colección que ve /estadisticas/tripulaciones."""
    await db_test.tripulaciones.insert_many(
        [
            {"nombre": "Piratas A"},
            {"nombre": "Piratas B"},
        ]
    )
    await db_test.tripulacions.insert_many(
        [{"nombre": f"Piratas {i}"} for i in range(5)]
    )

    res = await cliente_http.get("/estadisticas/tripulaciones/cantidad")
    res_tripulaciones = await cliente_http.get("/estadisticas/tripulaciones")

    assert res.status_code == 200
    assert res.json() == {"cantidad": 2}
    assert res_tripulaciones.status_code == 200
    assert res_tripulaciones.json()["total_tripulaciones"] == res.json()["cantidad"]


async def test_tripulaciones_cantidad_parametro_consulta_ignorado(cliente_http, db_test):
    """RF-1, RF-2: un parámetro de consulta se ignora sin alterar la respuesta."""
    await db_test.tripulaciones.insert_many(
        [
            {"nombre": "Piratas A"},
            {"nombre": "Piratas B"},
        ]
    )

    res = await cliente_http.get(
        "/estadisticas/tripulaciones/cantidad", params={"limite": "1", "x": "1"}
    )

    assert res.status_code == 200
    assert res.json() == {"cantidad": 2}
