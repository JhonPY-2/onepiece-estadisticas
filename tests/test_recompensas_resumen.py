# tests/test_recompensas_resumen.py
"""Tests del resumen global de recompensas.

T2: helpers de normalización y promedio (unitarios).
"""
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
