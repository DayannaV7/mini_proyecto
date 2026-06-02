# ─────────────────────────────────────────────────────────────
# db.py → Conexión a la base de datos
# Este archivo hace UNA sola cosa: conectar con la BD.
# Todos los demás archivos importan desde aquí cuando necesitan la BD.
# ─────────────────────────────────────────────────────────────

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv                          # lee el archivo .env
from sqlmodel import Session, create_engine, SQLModel
from fastapi import FastAPI, Depends
from typing import Annotated

load_dotenv()  # carga las variables del archivo .env (DATABASE_URL, etc.)

# Lee la URL de la base de datos desde el .env
# Ejemplo: postgresql://usuario:password@host/nombre_bd
DATABASE_URL = os.getenv("DATABASE_URL")

# Crea el "motor" de conexión a la base de datos
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# Esta función se ejecuta cuando arranca el servidor (lifespan).
# Crea las tablas en la BD si no existen.
# "app" recibe la aplicación FastAPI pero aquí no la usamos directamente.
@asynccontextmanager
async def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)  # crea las tablas automáticamente
    yield                                  # el servidor sigue corriendo


# Esta función abre una sesión (conexión temporal) con la BD.
# FastAPI la llama automáticamente en cada request gracias a Depends().
def get_session() -> Session:
    with Session(engine) as session:
        yield session  # entrega la sesión al endpoint que la pidió


# SessionDep es un "atajo" para no escribir Annotated[Session, Depends(get_session)]
# en cada endpoint. Se usa así: session: SessionDep
SessionDep = Annotated[Session, Depends(get_session)]