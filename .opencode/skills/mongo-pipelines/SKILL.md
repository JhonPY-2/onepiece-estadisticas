---
name: mongo-pipelines
description: Úsala siempre que escribas, modifiques o revises endpoints con pipelines de agregación, modelos de respuesta o tests de este microservicio
---

# Pipelines de agregación y endpoints de `/estadisticas`

## Reglas

1. Las referencias entre colecciones se guardan como `ObjectId`, no como texto. Para exponer nombres usa `$lookup` y, en el `$project`, `{"$ifNull": [{"$first": "$doc.nombre"}, None]}`; un `$group` a secas devuelve ids.
2. El nombre de la colección de tripulaciones se pide siempre a `coleccion_tripulaciones()`, que prueba `tripulaciones` y, si no existe, `tripulacions`. No escribas el nombre a mano.
3. Cada endpoint declara su modelo Pydantic y `response_model=...`; cuando el nombre viene de Mongo se expone con `Field(alias="_id")`, igual que `EquipoConteo` y `TripulacionConteo`.
4. Nada de datos puede romper la respuesta: una referencia sin documento relacionado se ignora y una base vacía devuelve total `0` y lista `[]`.
5. El conteo de miembros se calcula siempre: `numeroMiembros` está desactualizado y no se recalcula en ningún sitio.
6. Los endpoints usan el `db` del módulo, no una conexión propia, para que el monkeypatch de los tests aplique.
7. Entorno: `.venv-wsl` en WSL y `pytest -v` desde la raíz.

## Checklist de revisión

- [ ] El pipeline resuelve nombres con `$lookup` en vez de devolver ids crudos.
- [ ] La colección de tripulaciones se pide con `coleccion_tripulaciones()`, sin escribir el nombre a mano.
- [ ] Hay modelo Pydantic con `response_model` y `alias="_id"` donde corresponde.
- [ ] Hay test con datos en forma real (`ObjectId` + documento en la colección) y no se tocó la constante `PERSONAJES` compartida.
- [ ] Hay test de base vacía (total `0`, lista `[]`) y test de referencia sin documento relacionado.
- [ ] Los tests usan el fixture `db_test`, que solo toca `onepiece_test`.
- [ ] El conteo viene del cálculo real, no de `numeroMiembros`.

## Al terminar

Indica qué puntos del checklist se comprobaron y con qué evidencia: pega la salida de `pytest -v` y señala qué test cubre cada punto. Lo que no hayas comprobado, dilo explícitamente.