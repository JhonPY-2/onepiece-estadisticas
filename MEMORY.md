# MEMORY.md — onepiece-estadisticas

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Microservicio FastAPI + Motor con `/estadisticas/personajes`, `/estadisticas/atletas`, `/estadisticas/tripulaciones` y `/estadisticas/resumen`, con tests aislados en `onepiece_test`.

## Decisiones (y por qué)

- En WSL se usa el entorno `.venv-wsl` (en lugar de la carpeta `venv`, que es la de Windows) para evitar mezclar entornos entre sistemas. Si `python3-venv` no está instalado, crear con `python3 -m venv --without-pip .venv-wsl` e instalar con `python3 -m pip --python .venv-wsl/bin/python install -r requirements.txt` (el flag va **antes** del subcomando).
- Instalar en `.venv-wsl` tarda (>10 min) porque el repo está en `/mnt/c` (drvfs). Para verificaciones rápidas se puede crear el venv en el disco ext4 de WSL (p. ej. `/tmp/...`) y lanzar `pytest -v` desde la raíz del repo; el resultado es idéntico.
- Los miembros de una tripulación son documentos de `personajes` **y** de `tripulantes`, igual que en `tripulacionController.js` del backend principal.
- La lista de tripulaciones parte de la colección de tripulaciones, no de los miembros: así salen también las que tienen 0 miembros.
- El nombre de la colección de tripulaciones se resuelve en runtime: la colección se llama `tripulacions` por la pluralización por defecto de Mongoose, y `coleccion_tripulaciones()` prueba `tripulaciones` primero por si se cambia el nombre.

## Aprendizajes y errores a evitar

- Los tests nunca deben tocar la base de desarrollo `onepiece` (verifican `db.name != main.db.name`).
- `personajes.tripulacion` es un `ObjectId`, no un texto: un `$group` devuelve ids, hace falta `$lookup` a la colección de tripulaciones para exponer el nombre. Los `PERSONAJES` de los tests con el texto "Sombrero de Paja" son solo para `/personajes` y `/resumen`.
- `tripulaciones.numeroMiembros` está desactualizado (15 y 11 guardados frente a 10 y 10 personajes reales) y no se recalcula en ningún sitio: no usarlo como fuente de verdad.
- En los 20 personajes de `onepiece`, `tripulacion` está guardado como `ObjectId` (verificado en la base, no solo en el esquema).
- La colección se llama `tripulacions` por la pluralización por defecto de Mongoose (verificado con mongoose 9.9.5: `Tripulacion.collection.name === "tripulacions"`); no es un error de nombre.
- `$first` (usado en el `$project` del `$lookup`) requiere MongoDB 4.4+.

## Próximos pasos

- (vacío por ahora)