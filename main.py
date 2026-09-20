from typing import List, Optional

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os


load_dotenv()


app = FastAPI()

cliente = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = cliente.get_default_database()


# ---------- Modelos de respuesta (Pydantic) ----------

class PersonajeMayorRecompensa(BaseModel):
    nombre: str
    recompensa: float


class EstadisticasPersonajes(BaseModel):
    total_personajes: int
    personaje_mayor_recompensa: Optional[PersonajeMayorRecompensa] = None


class EquipoConteo(BaseModel):
    # Mongo devuelve el nombre del equipo en "_id"; se conserva ese nombre en el JSON
    equipo: Optional[str] = Field(default=None, alias="_id")
    cantidad: int


class EstadisticasAtletas(BaseModel):
    total_atletas: int
    atletas_por_equipo: List[EquipoConteo]


class Resumen(BaseModel):
    total_personajes: int
    total_atletas: int
    personaje_mayor_recompensa: Optional[PersonajeMayorRecompensa] = None


# ---------- Endpoints ----------

@app.get("/")
async def raiz():
    return {"mensaje": "Microservicio de estadisticas funcionando"}


@app.get("/estadisticas/personajes", response_model=EstadisticasPersonajes)
async def estadisticas_personajes():
    total_personajes = await db.personajes.count_documents({})

    personaje_mayor_recompensa = await db.personajes.find_one(
        sort=[("recompensa", -1)]
    )

    mayor = None
    if personaje_mayor_recompensa:
        mayor = {
            "nombre": personaje_mayor_recompensa["nombre"],
            "recompensa": personaje_mayor_recompensa["recompensa"],
        }

    return {
        "total_personajes": total_personajes,
        "personaje_mayor_recompensa": mayor,
    }


@app.get("/estadisticas/atletas", response_model=EstadisticasAtletas)
async def estadisticas_atletas():
    total_atletas = await db.atletas.count_documents({})

    pipeline = [
        {"$group": {"_id": "$equipo", "cantidad": {"$sum": 1}}},
        {"$sort": {"cantidad": -1}}
    ]

    resultado_cursor = db.atletas.aggregate(pipeline)
    atletas_por_equipo = await resultado_cursor.to_list(length=None)

    return {
        "total_atletas": total_atletas,
        "atletas_por_equipo": atletas_por_equipo
    }


@app.get("/estadisticas/resumen", response_model=Resumen)
async def estadisticas_resumen():
    total_personajes = await db.personajes.count_documents({})
    total_atletas = await db.atletas.count_documents({})

    personaje_mayor_recompensa = await db.personajes.find_one(
        sort=[("recompensa", -1)]
    )

    mayor = None
    if personaje_mayor_recompensa:
        mayor = {
            "nombre": personaje_mayor_recompensa["nombre"],
            "recompensa": personaje_mayor_recompensa["recompensa"],
        }

    return {
        "total_personajes": total_personajes,
        "total_atletas": total_atletas,
        "personaje_mayor_recompensa": mayor,
    }
