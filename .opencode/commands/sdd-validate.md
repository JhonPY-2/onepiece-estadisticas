---
description: Validar spec requisito por requisito (sin modificar nada)
agent: plan
---

Use the skill: sdd

Recorre `specs/$1/spec.md` **requisito por requisito** (RF-01, RF-02, ...).

Para cada RF:
1. **Si es requisito de lógica o de datos**: indica qué test de **pytest** lo cubre (archivo y nombre exacto del test) y si el criterio queda **realmente verificado** o si el test es **débil** (ejemplos: usa `<=` cuando pide número exacto, verifica solo estructura genérica, no cubre caso límite, etc.).
2. **Si es requisito de API**: indica cómo se verifica con **Chrome DevTools** (solo lectura): método, ruta, código de estado y forma del JSON en `http://localhost:8000/docs`, y qué comando exacto debe correr el usuario desde PowerShell (`$env:MONGODB_URI="mongodb://127.0.0.1:27017/onepiece"; venv\Scripts\python.exe -m pytest -v`). Comprueba también los **casos límite** de **sin datos** (colección vacía).
3. Si algún RF **no está cubierto** o la verificación es **débil**, dilo **claramente**. **NO arregles nada**.

Al final:
- Comprueba los **criterios de finalización** de la spec.
- Da un **veredicto** claro: ¿la spec está cumplida? (Sí/No + justificación breve).

Notas: NO ejecutes pytest (solo lectura de spec, plan, tasks y tests existentes). El agente NO arranca el servidor. Si usas Chrome DevTools en `http://localhost:8000`, hazlo **solo con acciones de LECTURA** (GET) y si el servidor no responde, PARA y avisa.

$ARGUMENTS
