---
name: sdd
description: "Úsala siempre que trabajes con Spec-Driven Development en este proyecto (docs/constitution.md o cualquier archivo dentro de specs/): redactar, revisar o cambiar specs, planes y tareas, o implementar y validar tareas de una spec."
---

# Skill: Spec-Driven Development (SDD) para onepiece-estadisticas

Esta skill define el flujo obligatorio para trabajar con especificaciones en este repositorio, siguiendo los principios de `docs/constitution.md`.

## 1. Flujo obligatorio

El flujo debe respetarse estrictamente en este orden:

1. **Constitución** → Leer `docs/constitution.md` antes de empezar cualquier trabajo con specs.
2. **Spec** → Crear/revisar `specs/NNN-nombre/spec.md`. **La spec manda**.
3. **Clarificación** → Resolver dudas abiertas en la spec. **Nunca pasar a la siguiente fase sin aprobación explícita**.
4. **Plan** → Crear `specs/NNN-nombre/plan.md`.
5. **Tareas** → Crear `specs/NNN-nombre/tasks.md`.
6. **Implementación** → Implementar **una sola tarea cada vez** (tests primero → código → verificar respuesta HTTP → marcar tarea → parar).
7. **Validación** → Verificar que se cumplen todos los criterios de finalización de la spec.
8. **Cambio** → Un cambio de requisitos **siempre se hace primero en la spec**, luego en plan, luego en tareas, y **por último en el código**.

Reglas del flujo:
- Cada spec vive en `specs/NNN-nombre/` con **exactamente**: `spec.md`, `plan.md` y `tasks.md`.
- **Nunca pasar a la siguiente fase sin aprobación explícita**.
- La spec es el **QUÉ y el PORQUÉ**; no debe contener detalles de stack, nombres de archivos, frameworks o implementación.
- Al terminar cada fase, **actualizar `MEMORY.md`** (resumir estado, decisiones importantes con su porqué, errores a evitar). Mantenerlo breve.
- Si algo se convierte en regla permanente, proponer moverlo a `AGENTS.md` en lugar de dejarlo en `MEMORY.md`.
- **Sin commit**: no se hace commit en ninguna fase.

## 2. Plantilla de spec (`spec.md`)

Todo `spec.md` debe seguir esta estructura:

```markdown
# specs/NNN-nombre/spec.md

**Estado: borrador | aprobada | implementada**

## Contexto y objetivo
(Explicar el problema, el contexto del proyecto y el objetivo a alcanzar. QUÉ y PORQUÉ, no CÓMO)

## Usuarios
(Definir usuarios/actores afectados)

## Historias de usuario
- Como [usuario], quiero [acción], para [beneficio].

## Definiciones
(Términos relevantes para evitar ambigüedad)

## Requisitos funcionales (RF)
| ID | Requisito (en EARS) |
|---|--------------------|

## Requisitos no funcionales (RNF)
| ID | Requisito |
|---|-----------|

## Casos límite
(Listar casos límite relevantes)

## Fuera de alcance
(Qué NO se incluye en esta spec)

## Criterios de finalización
(Listar criterios verificables para considerar la spec completada/implementada)

## Dudas abiertas
- [NECESITA ACLARACIÓN] ...
```

Notas sobre la spec:
- **Estado** obligatorio con el formato exacto: `**Estado: borrador | aprobada | implementada**`.
- Requisitos funcionales deben escribirse **obligatoriamente en formato EARS** (ver sección 3).
- Sin palabras vagas ("adecuado", "correcto", "rápido", etc.). Todo debe ser verificable.
- **Requisitos de API**: redactarlos para ser verificables en el contrato HTTP — **método, ruta, código de estado y forma exacta del JSON**. Se pueden comprobar con el MCP de **Chrome DevTools** (solo lectura) en `http://localhost:8000/docs` o en la URL del endpoint.
- **Casos límite**: incluir siempre el estado **sin datos** (colección vacía → ceros/`None`/listas vacías) y la respuesta ante **parámetros inválidos** cuando aplique.

## 3. Requisitos en EARS (en español)

Todos los RF deben redactarse siguiendo el formato **EARS** (Easy Approach to Requirements Syntax), en español:

- **CUANDO** [evento/condición], **EL SISTEMA** [comportamiento/resultados]
- **SI** [condición], **ENTONCES** [respuesta/comportamiento]
- **MIENTRAS** [estado], **EL SISTEMA** [comportamiento]
- **EL SISTEMA SIEMPRE** [invariante/regla]

Requisitos en EARS deben ser **verificables**, inequívocos y sin ambigüedad. No usar lenguaje subjetivo.

## 4. Plan (`plan.md`)

Todo `plan.md` debe contener al menos:

1. **Archivos a crear/modificar y responsabilidades** (arquitectura del proyecto: `main.py` para app + modelos Pydantic + endpoints, `tests/` para los tests). Explicar qué responsabilidad tiene cada archivo o función.
2. **Lógica (algoritmo/pseudocódigo)** que cubra todos los RF.
3. **Decisiones técnicas justificadas**: tabla con columnas `Decisión`, `Justificación`, `Alternativa descartada`.
4. **Estrategia de tests y verificación**:
   - **Lógica y acceso a datos** → tests de integración con **pytest + pytest-asyncio + httpx** (`httpx.ASGITransport`), contra Mongo real, siempre con la base de pruebas `onepiece_test`. Indicar qué RF cubre cada test.
   - **Contrato HTTP** → se verifica con el MCP de **Chrome DevTools** (solo lectura, contra `http://localhost:8000`) revisando `/docs` y las respuestas de los endpoints.
   - No hay lint ni build; no se proponen.
5. **Mapeo RF → implementación/tests**: dejar claro qué parte cubre cada RF.

## 5. Tareas (`tasks.md`)

Formato obligatorio para cada tarea:

```markdown
- [ ] **Tn. Descripción breve y accionable.** RF-x, RF-y
  - Tests: (qué tests de pytest crear/ajustar, qué debe pasar en rojo/verde)
  - Código: (qué cambiar en qué archivos, siguiendo convenciones)
  - Hecho cuando: (criterio de completitud verificable)
```

Reglas para tareas:
- Máximo **10 tareas** por spec.
- Cada tarea debe tomar **máximo 20-30 minutos**.
- Incluir **RF cubiertos** explícitamente.
- Criterio "Hecho cuando:" debe ser **concreto y verificable** (no ambiguo). Para endpoints, verificable con el MCP de Chrome DevTools (método, ruta, código de estado y forma del JSON).
- Las tareas deben seguir orden lógico (tests primero donde aplique).

## 6. Implementación (regla crítica)

**Una sola tarea cada vez**. Para cada tarea:

1. **Escribir tests primero** (TDD). Dejar claro que **fallan** (antes de escribir código). **No ejecutarlos tú**.
2. **Escribir código** hasta que los tests cubran lo que pide la tarea.
3. **Verificar la lógica** contra lo especificado (sin sobreimplementar). No modificar código ajeno innecesariamente.
4. **Verificar el contrato HTTP con Chrome DevTools** cuando la tarea tenga requisitos de API: abrir `http://localhost:8000/docs` o la URL del endpoint, comprobar método, código de estado y JSON. **Solo acciones de LECTURA** (los endpoints de este microservicio son GET). Ir contando al usuario **qué se comprueba**.
5. **Marcar la tarea como completada** (`[x]`) **SOLO cuando yo confirme** que los tests pasan y las verificaciones son correctas.
6. **Parar** después de cada tarea. No pasar a la siguiente tarea sin confirmación.

Reglas de ejecución (operativas):
- **El agente NO ejecuta `pytest`**: yo lo corro desde **PowerShell**. El agente da el **comando exacto**: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v` (un test: `$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest tests/test_estadisticas.py -k "nombre" -v`).
- **La `MONGODB_URI` apunta a `onepiece`** (los tests solo la abren, no escriben ahí); los tests escriben únicamente en `onepiece_test`.
- **El agente NO arranca el servidor** (`uvicorn main:app`, puerto `8000`): yo lo tengo levantado en otra pestaña. Si `http://localhost:8000` no responde, **PARA y avisa**.
- **Regla de seguridad con Chrome DevTools**: el servidor del puerto `8000` puede estar conectado a la base real. Al probar la API, **solo acciones de LECTURA** (GET y revisar `/docs`). **NUNCA** crear, editar ni borrar datos. Si una spec necesita probar escrituras, pedir al usuario que levante el servidor contra la base de pruebas y **esperar su confirmación**.
- Respetar estrictamente `docs/constitution.md`, `AGENTS.md` y `MEMORY.md` en todo momento.

## 7. Validación y cambios

- **Validación**: comprobar que todos los criterios de finalización de la spec se cumplen antes de darla por `implementada`. Para requisitos de API, verificar con Chrome DevTools (solo lectura) e indicar el comando exacto de `pytest` que el usuario debe correr.
- **Cambios**: cualquier cambio de requisitos → spec primero → plan → tareas → código (último). Mantener trazabilidad RF ↔ tests ↔ código.
- Al cambiar cualquier fase, actualizar `spec.md/plan.md/tasks.md` coherentemente y reflejarlo en `MEMORY.md`.
