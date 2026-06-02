# ─────────────────────────────────────────────────────────────
# models/persona.py → Define la forma de los datos
#
# Un "modelo" le dice a Python (y a la BD) cómo se ve un objeto.
# SQLModel combina Pydantic (validación) + SQLAlchemy (base de datos).
#
# Pydantic valida que los datos sean correctos ANTES de guardarlos.
# Por ejemplo: edad debe ser un número, no puede ser "hola".
# ─────────────────────────────────────────────────────────────

from sqlmodel import SQLModel, Field
from typing import Optional


# ── Clase BASE: define los campos que el usuario llena ────────
# Esta clase NO crea tabla en la BD. Solo define la "forma".
# Se usa para recibir datos del formulario o del JSON.
class PersonaBase(SQLModel):
    nombre: str   = Field(min_length=2, max_length=64,
                          description="Nombre de la persona")
    edad:   int   = Field(gt=0, lt=120,
                          description="Edad en años")
    ciudad: str   = Field(min_length=2, max_length=64,
                          description="Ciudad de origen")


# ── Clase TABLE: esta SÍ crea una tabla en la BD ─────────────
# Hereda todos los campos de PersonaBase y agrega:
#   - id: clave primaria (se genera automáticamente)
#   - imagen_url: ruta de la foto (puede estar vacía)
#   - estado: "activo" o "inactivo" (para soft delete)
#
# table=True → SQLModel crea la tabla "persona" en la BD
class Persona(PersonaBase, table=True):
    id:         int | None = Field(default=None, primary_key=True)
    imagen_url: str | None = None          # URL de la foto (puede ser None)
    estado:     str        = Field(default="activo")


# ── Clase UPDATE: campos opcionales para editar ───────────────
# Todos los campos son opcionales (| None) porque al editar
# el usuario puede querer cambiar solo el nombre, o solo la edad.
class PersonaUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=64)
    edad:   int | None = Field(default=None, gt=0, lt=120)
    ciudad: str | None = Field(default=None, min_length=2, max_length=64)