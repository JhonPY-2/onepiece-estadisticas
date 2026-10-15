# tests/conftest.py
"""Guardas globales y fixtures compartidas de la suite de tests."""

import os

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

import main  # al importarlo, main.py ejecuta load_dotenv() y carga tu .env

BASE_DE_PRUEBAS = "onepiece_test"
NOMBRE_DB_TEST = BASE_DE_PRUEBAS


def pytest_collection_modifyitems(session, config, items):
    """Aborta la suite si algún test apunta a una base distinta de la de pruebas.

    Los tests sólo pueden escribir en `onepiece_test`. Nunca en la base real
    `onepiece`.
    """
    for item in items:
        modulo = getattr(item, "module", None)
        nombre_db = getattr(modulo, "NOMBRE_DB_TEST", None)
        if nombre_db is None:
            continue
        if nombre_db != BASE_DE_PRUEBAS:
            raise pytest.UsageError(
                "Los tests solo pueden correr contra la base de pruebas "
                f"'{BASE_DE_PRUEBAS}', pero apuntan a '{nombre_db}'. "
                "Nunca se permite ejecutar tests contra la base real 'onepiece'."
            )


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
