# tests/test_estadisticas.py
import os

import httpx
import pytest
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

import main  # al importarlo, main.py ejecuta load_dotenv() y carga tu .env

NOMBRE_DB_TEST = "onepiece_test"

PERSONAJES = [
    {"nombre": "Monkey D. Luffy", "recompensa": 3000000000, "tripulacion": "Sombrero de Paja"},
    {"nombre": "Roronoa Zoro", "recompensa": 1111000000, "tripulacion": "Sombrero de Paja"},
    {"nombre": "Nami", "recompensa": 366000000, "tripulacion": "Sombrero de Paja"},
]

ATLETAS = [
    {"nombre": "Atleta 1", "equipo": "Equipo A"},
    {"nombre": "Atleta 2", "equipo": "Equipo A"},
    {"nombre": "Atleta 3", "equipo": "Equipo B"},
    {"nombre": "Atleta 4", "equipo": "Equipo C"},
]

# En la base real personajes.tripulacion es un ObjectId que apunta a la colección
# de tripulaciones (no un texto), así que los tests de tripulaciones lo replican
ID_PAJA = ObjectId("6ab49840bf5269d5b9e9afa8")
ID_BARBANEGRA = ObjectId("6ab34fb62f4472871fb4a62e")
ID_SIN_DOCUMENTO = ObjectId("000000000000000000000001")

TRIPULACIONES = [
    {"_id": ID_PAJA, "nombre": "Piratas de Sombrero de Paja", "capitan": "Monkey D. Luffy", "numeroMiembros": 11},
    {"_id": ID_BARBANEGRA, "nombre": "Piratas de Barbanegra", "capitan": "Marshall D. Teach", "numeroMiembros": 15},
]

PERSONAJES_CON_TRIPULACION = [
    {"nombre": "Monkey D. Luffy", "recompensa": 3000000000, "tripulacion": ID_PAJA},
    {"nombre": "Roronoa Zoro", "recompensa": 1111000000, "tripulacion": ID_PAJA},
    {"nombre": "Marshall D. Teach", "recompensa": 0, "tripulacion": ID_BARBANEGRA},
]

TRIPULANTES = [
    {"nombre": "Nami", "tripulacion": ID_PAJA},
    {"nombre": "Sanji", "tripulacion": ID_PAJA},
    {"nombre": "Hachi", "tripulacion": ID_BARBANEGRA},
]


@pytest.fixture
async def db_test(monkeypatch):
    """Base de datos de prueba: vacía al empezar y borrada al terminar."""
    cliente = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = cliente[NOMBRE_DB_TEST]

    # Seguro: jamás trabajar sobre tu base de datos real
    assert db.name != main.db.name

    await cliente.drop_database(NOMBRE_DB_TEST)
    monkeypatch.setattr(main, "db", db)  # main.py ahora usa la BD de prueba

    yield db

    await cliente.drop_database(NOMBRE_DB_TEST)
    cliente.close()


@pytest.fixture
async def cliente_http(db_test):
    """Cliente que llama a tu app FastAPI directamente, sin levantar uvicorn."""
    transporte = httpx.ASGITransport(app=main.app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transporte, base_url="http://test") as cliente:
        yield cliente


async def test_raiz(cliente_http):
    res = await cliente_http.get("/")

    assert res.status_code == 200
    assert res.json() == {"mensaje": "Microservicio de estadisticas funcionando"}


async def test_estadisticas_personajes(cliente_http, db_test):
    await db_test.personajes.insert_many([dict(p) for p in PERSONAJES])

    res = await cliente_http.get("/estadisticas/personajes")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_personajes"] == 3
    assert datos["personaje_mayor_recompensa"] == {
        "nombre": "Monkey D. Luffy",
        "recompensa": 3000000000,
    }


async def test_estadisticas_atletas_agrupa_por_equipo(cliente_http, db_test):
    await db_test.atletas.insert_many([dict(a) for a in ATLETAS])

    res = await cliente_http.get("/estadisticas/atletas")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_atletas"] == 4

    por_equipo = {e["_id"]: e["cantidad"] for e in datos["atletas_por_equipo"]}
    assert por_equipo == {"Equipo A": 2, "Equipo B": 1, "Equipo C": 1}

    # El $sort descendente deja primero al equipo con más atletas
    assert datos["atletas_por_equipo"][0]["_id"] == "Equipo A"


async def test_estadisticas_resumen(cliente_http, db_test):
    await db_test.personajes.insert_many([dict(p) for p in PERSONAJES])
    await db_test.atletas.insert_many([dict(a) for a in ATLETAS])

    res = await cliente_http.get("/estadisticas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_personajes"] == 3
    assert datos["total_atletas"] == 4
    assert datos["personaje_mayor_recompensa"]["nombre"] == "Monkey D. Luffy"
    assert datos["personaje_mayor_recompensa"]["recompensa"] == 3000000000


async def test_personajes_sin_datos_no_rompe(cliente_http):
    res = await cliente_http.get("/estadisticas/personajes")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_personajes"] == 0
    assert datos["personaje_mayor_recompensa"] is None


async def test_resumen_sin_datos_no_rompe(cliente_http):
    res = await cliente_http.get("/estadisticas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_personajes"] == 0
    assert datos["total_atletas"] == 0
    assert datos["personaje_mayor_recompensa"] is None


async def test_estadisticas_tripulaciones_cuenta_personajes_y_tripulantes(cliente_http, db_test):
    await db_test.tripulaciones.insert_many([dict(t) for t in TRIPULACIONES])
    await db_test.personajes.insert_many([dict(p) for p in PERSONAJES_CON_TRIPULACION])
    await db_test.tripulantes.insert_many([dict(t) for t in TRIPULANTES])

    res = await cliente_http.get("/estadisticas/tripulaciones")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_tripulaciones"] == 2

    # El $lookup convierte el ObjectId en el nombre real de la tripulación
    por_tripulacion = {t["_id"]: t["cantidad"] for t in datos["tripulaciones_por_nombre"]}
    assert por_tripulacion == {
        "Piratas de Sombrero de Paja": 4,  # 2 personajes + 2 tripulantes
        "Piratas de Barbanegra": 2,  # 1 personaje + 1 tripulante
    }

    assert datos["tripulaciones_por_nombre"][0]["_id"] == "Piratas de Sombrero de Paja"


async def test_estadisticas_tripulaciones_incluye_las_sin_miembros(cliente_http, db_test):
    await db_test.tripulaciones.insert_many([dict(t) for t in TRIPULACIONES])

    res = await cliente_http.get("/estadisticas/tripulaciones")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_tripulaciones"] == 2
    assert {t["_id"]: t["cantidad"] for t in datos["tripulaciones_por_nombre"]} == {
        "Piratas de Sombrero de Paja": 0,
        "Piratas de Barbanegra": 0,
    }


async def test_estadisticas_tripulaciones_ignora_tripulacion_sin_documento(cliente_http, db_test):
    await db_test.tripulaciones.insert_many([dict(t) for t in TRIPULACIONES])
    await db_test.personajes.insert_one(
        {"nombre": "Sin tripulación", "recompensa": 1, "tripulacion": ID_SIN_DOCUMENTO}
    )

    res = await cliente_http.get("/estadisticas/tripulaciones")

    assert res.status_code == 200
    datos = res.json()
    por_tripulacion = {t["_id"]: t["cantidad"] for t in datos["tripulaciones_por_nombre"]}
    assert por_tripulacion == {"Piratas de Sombrero de Paja": 0, "Piratas de Barbanegra": 0}


async def test_tripulaciones_sin_datos_no_rompe(cliente_http):
    res = await cliente_http.get("/estadisticas/tripulaciones")

    assert res.status_code == 200
    datos = res.json()
    assert datos["total_tripulaciones"] == 0
    assert datos["tripulaciones_por_nombre"] == []