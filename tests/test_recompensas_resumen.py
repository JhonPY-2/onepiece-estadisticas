# tests/test_recompensas_resumen.py
"""Tests del resumen global de recompensas.

T2: helpers de normalización y promedio (unitarios).
T3: modelo de respuesta y endpoint con colección vacía (integración).
"""
import pytest

import main

NOMBRE_DB_TEST = "onepiece_test"


# ---------- normalizar_recompensa ----------

def test_normalizar_recompensa_none_es_cero():
    assert main.normalizar_recompensa(None) == 0


def test_normalizar_recompensa_entero_tal_cual():
    assert main.normalizar_recompensa(1000) == 1000


def test_normalizar_recompensa_medio_hacia_arriba():
    assert main.normalizar_recompensa(1.5) == 2


def test_normalizar_recompensa_fraccion_baja():
    assert main.normalizar_recompensa(2.4) == 2


def test_normalizar_recompensa_fraccion_alta():
    assert main.normalizar_recompensa(1500.7) == 1501


def test_normalizar_recompensa_cero():
    assert main.normalizar_recompensa(0) == 0


# ---------- promedio_recompensas ----------

def test_promedio_recompensas_medio_hacia_arriba():
    assert main.promedio_recompensas(3, 2) == 2


def test_promedio_recompensas_entero_exacto():
    assert main.promedio_recompensas(2, 2) == 1


def test_promedio_recompensas_otro_medio_hacia_arriba():
    assert main.promedio_recompensas(5, 2) == 3


def test_promedio_recompensas_total_cero():
    assert main.promedio_recompensas(0, 3) == 0


def test_promedio_recompensas_fraccion_baja():
    assert main.promedio_recompensas(4, 3) == 1


def test_promedio_recompensas_sin_personajes():
    assert main.promedio_recompensas(10, 0) == 0


# ---------- T3: integración con colección vacía ----------

async def test_recompensas_resumen_coleccion_vacia(cliente_http):
    """GET /estadisticas/recompensas/resumen con colección vacía → 200 y cinco ceros."""
    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos == {
        "cantidad_personajes": 0,
        "total_recompensas": 0,
        "promedio_recompensa": 0,
        "recompensa_maxima": 0,
        "recompensa_minima": 0,
    }
    # Exactamente 5 campos, sin extras
    assert set(datos.keys()) == {
        "cantidad_personajes",
        "total_recompensas",
        "promedio_recompensa",
        "recompensa_maxima",
        "recompensa_minima",
    }


async def test_recompensas_resumen_post_no_permitido(cliente_http):
    """POST a la misma ruta → 405."""
    res = await cliente_http.post("/estadisticas/recompensas/resumen", json={})
    assert res.status_code == 405


async def test_recompensas_resumen_put_no_permitido(cliente_http):
    """PUT a la misma ruta → 405."""
    res = await cliente_http.put("/estadisticas/recompensas/resumen", json={})
    assert res.status_code == 405


# ---------- T4: Contar personajes y agregar total, máxima y mínima ----------

async def test_recompensas_resumen_dos_recompensas_enteras(cliente_http, db_test):
    """Dos recompensas enteras → cantidad=2, total, max, min correctos."""
    await db_test.personajes.insert_many([
        {"nombre": "Monkey D. Luffy", "recompensa": 3000000000},
        {"nombre": "Roronoa Zoro", "recompensa": 1000000000},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 2
    assert datos["total_recompensas"] == 4000000000
    assert datos["recompensa_maxima"] == 3000000000
    assert datos["recompensa_minima"] == 1000000000
    assert datos["promedio_recompensa"] == 2000000000


async def test_recompensas_resumen_recompensa_cero_participa_en_minimo(cliente_http, db_test):
    """recompensa: 0 cuenta en cantidad, total y como mínimo."""
    await db_test.personajes.insert_many([
        {"nombre": "Personaje A", "recompensa": 1000},
        {"nombre": "Personaje B", "recompensa": 0},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 2
    assert datos["total_recompensas"] == 1000
    assert datos["recompensa_maxima"] == 1000
    assert datos["recompensa_minima"] == 0


async def test_recompensas_resumen_null_y_ausente_cuentan_como_cero(cliente_http, db_test):
    """null y campo ausente cuentan como 0 y participan en max/min."""
    await db_test.personajes.insert_many([
        {"nombre": "Con recompensa", "recompensa": 5000},
        {"nombre": "Sin recompensa (null)", "recompensa": None},
        {"nombre": "Sin campo recompensa"},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 3
    assert datos["total_recompensas"] == 5000
    assert datos["recompensa_maxima"] == 5000
    assert datos["recompensa_minima"] == 0


async def test_recompensas_resumen_no_entero_se_redondea_antes_de_agregar(cliente_http, db_test):
    """Valores no enteros se redondean (half up) antes de sumar y comparar."""
    await db_test.personajes.insert_many([
        {"nombre": "A", "recompensa": 1.5},   # → 2
        {"nombre": "B", "recompensa": 2.4},   # → 2
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 2
    assert datos["total_recompensas"] == 4
    assert datos["recompensa_maxima"] == 2
    assert datos["recompensa_minima"] == 2
