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


class TripulacionConteo(BaseModel):
    # Mongo devuelve el nombre de la tripulación en "_id"; se conserva ese nombre en el JSON
    tripulacion: Optional[str] = Field(default=None, alias="_id")
    cantidad: int


class EstadisticasTripulaciones(BaseModel):
    total_tripulaciones: int
    tripulaciones_por_nombre: List[TripulacionConteo]


class Resumen(BaseModel):
    total_personajes: int
    total_atletas: int
    personaje_mayor_recompensa: Optional[PersonajeMayorRecompensa] = None


# ---------- Endpoints ----------

async def coleccion_tripulaciones(existentes: list) -> str:
    """La colección se llama 'tripulacions' por la pluralización por defecto de Mongoose.

    Se prueba primero 'tripulaciones' por si algún día se cambia el nombre, para
    que el $lookup siga funcionando en cualquiera de los dos casos.
    """
    for nombre in ("tripulaciones", "tripulacions"):
        if nombre in existentes:
            return nombre
    return "tripulaciones"


async def conteo_miembros(coleccion_miembros: str, coleccion_ref: str) -> dict:
    """Agrupa una colección de miembros por tripulacion y resuelve el nombre real."""
    pipeline = [
        {"$group": {"_id": "$tripulacion", "cantidad": {"$sum": 1}}},
        {
            "$lookup": {
                "from": coleccion_ref,
                "localField": "_id",
                "foreignField": "_id",
                "as": "tripulacion_doc",
            }
        },
        {
            "$project": {
                "_id": 1,
                "cantidad": 1,
                "nombre": {"$ifNull": [{"$first": "$tripulacion_doc.nombre"}, None]},
            }
        },
    ]

    cursor = db[coleccion_miembros].aggregate(pipeline)
    return {d["nombre"]: d["cantidad"] for d in await cursor.to_list(length=None)}


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


@app.get("/estadisticas/tripulaciones", response_model=EstadisticasTripulaciones)
async def estadisticas_tripulaciones():
    existentes = await db.list_collection_names()
    coleccion = await coleccion_tripulaciones(existentes)

    # La base son todas las tripulaciones, así que también salen las que no tienen miembros
    cursor = db[coleccion].find({}, {"nombre": 1})
    tripulaciones = await cursor.to_list(length=None)
    conteos = {t["nombre"]: 0 for t in tripulaciones}

    # El backend considera miembros tanto a personajes como a tripulantes
    colecciones_miembros = ["personajes", "tripulantes"]
    for coleccion_miembros in colecciones_miembros:
        if coleccion_miembros in existentes:
            for nombre, cantidad in (await conteo_miembros(coleccion_miembros, coleccion)).items():
                if nombre in conteos:
                    conteos[nombre] += cantidad

    tripulaciones_por_nombre = [
        {"_id": nombre, "cantidad": cantidad}
        for nombre, cantidad in sorted(conteos.items(), key=lambda i: -i[1])
    ]

    return {
        "total_tripulaciones": len(tripulaciones),
        "tripulaciones_por_nombre": tripulaciones_por_nombre,
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
