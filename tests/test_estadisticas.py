# tests/test_estadisticas.py
import os

import httpx
import pytest
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