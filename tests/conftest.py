# tests/conftest.py
"""Guardas globales de la suite de tests."""

import pytest


BASE_DE_PRUEBAS = "onepiece_test"


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
