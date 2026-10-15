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


# ---------- T5: Calcular el promedio con aritmética entera ----------

async def test_recompensas_resumen_promedio_medio_hacia_arriba(cliente_http, db_test):
    """Promedio con fracción .5 → redondea hacia arriba (1.5 → 2)."""
    await db_test.personajes.insert_many([
        {"nombre": "A", "recompensa": 1},
        {"nombre": "B", "recompensa": 2},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 2
    assert datos["total_recompensas"] == 3
    assert datos["promedio_recompensa"] == 2


async def test_recompensas_resumen_promedio_otro_medio_hacia_arriba(cliente_http, db_test):
    """Otro caso promedio .5 → hacia arriba (2.5 → 3)."""
    await db_test.personajes.insert_many([
        {"nombre": "A", "recompensa": 0},
        {"nombre": "B", "recompensa": 5},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 2
    assert datos["total_recompensas"] == 5
    assert datos["promedio_recompensa"] == 3


async def test_recompensas_resumen_promedio_enteros_grandes(cliente_http, db_test):
    """Promedio con enteros grandes (Luffy/Zoro) → 2000000000."""
    await db_test.personajes.insert_many([
        {"nombre": "Monkey D. Luffy", "recompensa": 3000000000},
        {"nombre": "Roronoa Zoro", "recompensa": 1000000000},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 2
    assert datos["total_recompensas"] == 4000000000
    assert datos["promedio_recompensa"] == 2000000000


# ---------- T6: Casos límite: sin recompensas y un solo personaje ----------


async def test_recompensas_resumen_sin_recompensas_cuatro_campos_cero(cliente_http, db_test):
    """3 personajes sin recompensa/null → cantidad > 0 y los otros cuatro en 0."""
    await db_test.personajes.insert_many([
        {"nombre": "A"},
        {"nombre": "B", "recompensa": None},
        {"nombre": "C", "recompensa": 0},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 3
    assert datos["total_recompensas"] == 0
    assert datos["promedio_recompensa"] == 0
    assert datos["recompensa_maxima"] == 0
    assert datos["recompensa_minima"] == 0


async def test_recompensas_resumen_unico_personaje_con_decimal_redondeado(cliente_http, db_test):
    """Un único personaje con 1500.7 → todos coherentes con 1501."""
    await db_test.personajes.insert_many([
        {"nombre": "Único", "recompensa": 1500.7},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 1
    assert datos["total_recompensas"] == 1501
    assert datos["promedio_recompensa"] == 1501
    assert datos["recompensa_maxima"] == 1501
    assert datos["recompensa_minima"] == 1501


async def test_recompensas_resumen_unico_personaje_sin_recompensa(cliente_http, db_test):
    """Un único personaje sin recompensa → cantidad=1 y resto 0."""
    await db_test.personajes.insert_many([
        {"nombre": "Único"},
    ])

    res = await cliente_http.get("/estadisticas/recompensas/resumen")

    assert res.status_code == 200
    datos = res.json()
    assert datos["cantidad_personajes"] == 1
    assert datos["total_recompensas"] == 0
    assert datos["promedio_recompensa"] == 0
    assert datos["recompensa_maxima"] == 0
    assert datos["recompensa_minima"] == 0
