# onepiece-estadisticas

Microservicio de estadísticas (FastAPI + Motor + Pydantic) de One Piece App. Calcula totales y agregaciones contra MongoDB (mayor recompensa, atletas por equipo) y los expone bajo `/estadisticas/*`.

## Correrlo

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Documentación automática en http://localhost:8000/docs. Configuración: copia `.env.example` a `.env` con la `MONGODB_URI` (la misma base que el backend).

## Tests

```
pytest -v
```

> Consulta el README principal del proyecto en [README principal (repositorio mongo-crud)](https://github.com/JhonPY-2/mongo-crud).