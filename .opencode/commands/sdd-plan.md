---
description: Generar plan.md para una spec
agent: plan
---

Use the skill: sdd

Genera `specs/$1/plan.md` siguiendo exactamente la plantilla/estructura de la skill sdd.

Requisitos previos:
- `specs/$1/spec.md` debe existir.
- Si la spec no está **aprobada** o tiene alguna entrada con `[NECESITA ACLARACIÓN]`, **PARA y avisa**. No generes plan.

Contenido obligatorio según skill:
1. Archivos a crear/modificar y responsabilidades (arquitectura del proyecto: `main.py` para app + modelos Pydantic + endpoints, `tests/` para los tests)
2. Lógica (algoritmo/pseudocódigo) que cubra todos los RF
3. Decisiones técnicas justificadas (tabla: Decisión, Justificación, Alternativa descartada)
4. Estrategia de tests y verificación: **lógica y datos** con tests de integración en **pytest + pytest-asyncio + httpx** contra Mongo real, siempre con la base de pruebas `onepiece_test`; **contrato HTTP** con el MCP de **Chrome DevTools** (solo lectura, contra `http://localhost:8000`). Indicar qué RF cubre cada test. No hay lint ni build.
5. Mapeo RF → implementación/tests

El agente NO ejecuta pytest ni arranca uvicorn: el usuario los corre desde PowerShell.

$ARGUMENTS
