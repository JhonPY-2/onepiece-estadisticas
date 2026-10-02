# MEMORY.md — onepiece-estadisticas

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Microservicio FastAPI + Motor que expone `/estadisticas/personajes`, `/estadisticas/atletas` y `/estadisticas/resumen`, con tests aislados en la base `onepiece_test`.

## Decisiones (y por qué)

- En WSL se usa el entorno `.venv-wsl` (en lugar de la carpeta `venv`, que es la de Windows) para evitar mezclar entornos entre sistemas.

## Aprendizajes y errores a evitar

- Los tests nunca deben tocar la base de desarrollo `onepiece` (verifican `db.name != main.db.name`).

## Próximos pasos

- (vacío por ahora)