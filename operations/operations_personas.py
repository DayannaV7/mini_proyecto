# ─────────────────────────────────────────────────────────────
# operations/operations_personas.py → Habla con la base de datos
#
# Este archivo contiene las funciones CRUD:
#   C → Create  (crear)
#   R → Read    (leer)
#   U → Update  (actualizar)
#   D → Delete  (eliminar)
#
# Estas funciones NO saben nada de HTTP ni de HTML.
# Solo reciben datos, los guardan/consultan en la BD, y retornan resultados.
# main.py las llama cuando llega una petición del usuario.
# ─────────────────────────────────────────────────────────────

from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select
from models.persona import Persona, PersonaBase, PersonaUpdate


# ── CREATE: Guardar una persona nueva en la BD ────────────────
def crear_persona(datos: PersonaBase, session: Session) -> Persona:
    # model_validate convierte PersonaBase → Persona (agrega id, estado, etc.)
    nueva = Persona.model_validate(datos)
    session.add(nueva)      # prepara el INSERT
    session.commit()        # ejecuta el INSERT en la BD
    session.refresh(nueva)  # recarga para obtener el id generado
    return nueva


# ── READ: Traer todas las personas activas ────────────────────
def ver_personas(session: Session) -> list[Persona]:
    # select(Persona) → SELECT * FROM persona
    # .where(...) → WHERE estado = 'activo'
    return list(session.exec(
        select(Persona).where(Persona.estado == "activo")
    ).all())


# ── READ: Buscar una persona por su ID ───────────────────────
def buscar_por_id(id: int, session: Session) -> Persona | None:
    try:
        return session.get_one(Persona, id)  # SELECT WHERE id = ?
    except NoResultFound:
        return None  # si no existe, retorna None (main.py devuelve 404)


# ── UPDATE: Editar campos de una persona ─────────────────────
def editar_persona(id: int, datos: PersonaUpdate, session: Session) -> Persona | None:
    persona = buscar_por_id(id, session)
    if not persona or persona.estado == "inactivo":
        return None  # no existe o está inactiva

    # exclude_unset=True → solo actualiza los campos que el usuario envió
    # Si el usuario solo envió "edad", solo cambia la edad, no el nombre ni ciudad
    campos = datos.model_dump(exclude_unset=True)
    persona.sqlmodel_update(campos)  # aplica los cambios al objeto
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona


# ── UPDATE: Guardar la URL de la imagen ──────────────────────
def actualizar_imagen(id: int, url: str, session: Session) -> Persona | None:
    persona = buscar_por_id(id, session)
    if not persona:
        return None
    persona.imagen_url = url   # actualiza solo la imagen
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona


# ── DELETE (soft): Marcar como inactiva en lugar de borrar ───
# "Soft delete" = no borramos el registro, solo cambiamos estado a "inactivo"
# Así conservamos el historial y podemos recuperar los datos si es necesario
def desactivar_persona(id: int, session: Session) -> Persona | None:
    persona = buscar_por_id(id, session)
    if not persona:
        return None
    persona.estado = "inactivo"  # UPDATE estado = 'inactivo'
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona