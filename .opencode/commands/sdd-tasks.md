---
description: Generar tasks.md para una spec
agent: plan
---

Use the skill: sdd

Genera `specs/$1/tasks.md` siguiendo la skill sdd.

Reglas:
- Máximo **10 tareas** por spec. Si salen más, **propón dividir la spec**.
- Cada tarea: máximo 20-30 minutos.
- Formato: `- [ ] **Tn. Descripción.** RF-x, RF-y` con línea `  - Hecho cuando: ...`
- Incluir Tests (pytest, en `tests/`), Código y Hecho cuando.
- Para tareas con endpoints, el "Hecho cuando" debe ser **verificable con Chrome DevTools**: método, ruta, código de estado y forma del JSON (solo lectura, contra `http://localhost:8000/docs`).
- Orden lógico (tests primero donde aplique).

$ARGUMENTS
