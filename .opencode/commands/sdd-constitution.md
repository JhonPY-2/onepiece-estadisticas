---
description: Revisar docs/constitution.md (si existe) y proponer 6 principios innegociables
agent: plan
---

Crea un borrador de **6 principios innegociables** para este proyecto, basándote en lo que ya exista en `docs/constitution.md` (si no existe, propón los principios revisando el código). **No escribas ni modifiques ningún archivo hasta que yo te dé mi aprobación explícita.**

Antes de proponer, lee `AGENTS.md`, `MEMORY.md` y al menos los archivos principales del código (`main.py`, `tests/test_estadisticas.py`, `requirements.txt`, `pytest.ini`). Ten en cuenta: este es un microservicio **FastAPI + Motor + Pydantic** (Python) en `http://localhost:8000` que expone `/estadisticas/*` y que consume `onepiece-app` por HTTP.

Los 6 principios deben cubrir, en este orden:
1. **Simplicidad del stack** (FastAPI + Motor + Pydantic, sin sobre-ingeniería).
2. **Relación spec-código** (la spec manda; el código y la doc deben reflejarla).
3. **Separación de responsabilidades en `main.py`** (modelos Pydantic, helpers de agregación y endpoints claramente separados).
4. **Política de tests y verificación** (pytest + pytest-asyncio + httpx contra Mongo real, sólo contra `onepiece_test`; el contrato HTTP se verifica con Chrome DevTools).
5. **Datos protegidos** (microservicio de solo lectura; nunca `drop`/`delete` sobre la base real `onepiece`).
6. **Idioma español** (textos, comentarios, documentación y mensajes).

Máximo **15 líneas**.

$ARGUMENTS
