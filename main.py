#píp install -r requirements.txt
#.\.venv\Scripts\python.exe -m uvicorn main:app --reload


# ─────────────────────────────────────────────────────────────
# main.py → El archivo central. Define TODAS las rutas (endpoints).
#
# Hay 3 tipos de rutas en este proyecto:
#
#   1. RUTAS HTML → el navegador las abre y recibe una página web
#      Ejemplo: GET /personas → muestra personas.html con las cards
#
#   2. RUTAS DE FORMULARIO → reciben datos de un <form> HTML y redirigen
#      Ejemplo: POST /form/personas → crea persona y vuelve a /personas
#
#   3. RUTAS API (JSON) → el JavaScript las llama con fetch()
#      Ejemplo: PATCH /api/personas/1 → edita persona y retorna JSON
#
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles       # sirve archivos CSS, JS, imágenes
from fastapi.templating import Jinja2Templates    # renderiza HTML con datos de Python

from db import create_all_tables, SessionDep
from models.persona import PersonaBase, PersonaUpdate
from operations.operations_personas import (
    crear_persona,
    ver_personas,
    buscar_por_id,
    editar_persona,
    actualizar_imagen,
    desactivar_persona
)
# Sube las imágenes al bucket de Supabase y devuelve su URL pública
from storage import subir_imagen_a_supabase

# ── Crear la aplicación FastAPI ───────────────────────────────
# lifespan=create_all_tables → cuando arranca el servidor, crea las tablas en la BD
app = FastAPI(
    lifespan=create_all_tables,
    title="Mini Web API",
    description="Proyecto mínimo para entender FastAPI + HTML + CSS + JS"
)

# ── Archivos estáticos (CSS, JS, imágenes) ───────────────────
# Esto le dice a FastAPI: "sirve los archivos de la carpeta 'static'
# cuando alguien pida /static/algo"
# En el HTML se usan así: <link href="/static/css/style.css">
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Templates Jinja2 ─────────────────────────────────────────
# Le dice a FastAPI dónde están los archivos HTML.
# Jinja2 permite meter datos de Python dentro del HTML usando {{ variable }}
templates = Jinja2Templates(directory="templates")

# Las imágenes ya NO se guardan en disco: se suben a Supabase Storage
# (ver storage.py). Por eso aquí ya no creamos la carpeta static/imgs.


# ══════════════════════════════════════════════════════════════
#  RUTAS HTML → devuelven páginas completas al navegador
# ══════════════════════════════════════════════════════════════

# GET / → Página de inicio
# response_class=HTMLResponse → le dice a FastAPI que la respuesta es HTML
@app.get("/", response_class=HTMLResponse, tags=["HTML"])
def inicio(request: Request):
    # TemplateResponse renderiza el archivo HTML y lo envía al navegador
    # "request" siempre se necesita para que Jinja2 funcione
    return templates.TemplateResponse("index.html", {
        "request": request   # Jinja2 necesita el request para funcionar
    })


# GET /personas → Página con todas las personas (cards)
@app.get("/personas", response_class=HTMLResponse, tags=["HTML"])
def pagina_personas(
    request: Request,
    session: SessionDep,
    mensaje: str = "",           # mensaje flash (viene en la URL después de crear/editar)
    tipo_mensaje: str = "success"  # "success" = verde, "danger" = rojo
):
    # 1. Trae las personas de la BD usando la función de operations/
    personas = ver_personas(session)

    # 2. Renderiza el HTML pasándole las personas y el mensaje
    #    En el HTML se accede así: {% for p in personas %} o {{ mensaje }}
    return templates.TemplateResponse("personas.html", {
        "request":      request,
        "personas":     personas,    # lista de personas activas
        "mensaje":      mensaje,     # ej: "Persona creada exitosamente"
        "tipo_mensaje": tipo_mensaje # "success" o "danger"
    })


# ══════════════════════════════════════════════════════════════
#  RUTAS DE FORMULARIO → reciben datos del <form> HTML
#  Siempre terminan con RedirectResponse para volver a la página
# ══════════════════════════════════════════════════════════════

# POST /form/personas → Crea una persona desde el formulario HTML
# Los datos vienen del <form> con method="post" action="/form/personas"
# Form(...) extrae cada campo del formulario
@app.post("/form/personas", tags=["Formularios"])
async def form_crear_persona(
    session:  SessionDep,
    nombre:   str         = Form(...),   # campo obligatorio del formulario
    edad:     int         = Form(...),
    ciudad:   str         = Form(...),
    imagen:   UploadFile  = File(None)   # archivo opcional
):
    # 1. Crea el objeto base con los datos del formulario
    base = PersonaBase(nombre=nombre, edad=edad, ciudad=ciudad)

    # 2. Guarda en la BD usando la función de operations/
    nueva = crear_persona(base, session)

    # 3. Si el usuario subió una imagen, la subimos a Supabase Storage
    if imagen and imagen.filename:
        contenido = await imagen.read()  # lee los bytes del archivo subido
        url = subir_imagen_a_supabase(
            contenido, imagen.filename, imagen.content_type
        )
        # Guarda en la BD la URL pública que devuelve Supabase
        actualizar_imagen(nueva.id, url, session)

    # 4. Redirige de vuelta a /personas con un mensaje de éxito
    # status_code=303 → el navegador hace GET /personas (no repite el POST)
    return RedirectResponse(
        f"/personas?mensaje=Persona+creada+exitosamente",
        status_code=303
    )


# ══════════════════════════════════════════════════════════════
#  RUTAS API (JSON) → las llama JavaScript con fetch()
#  No devuelven HTML, devuelven datos en formato JSON
# ══════════════════════════════════════════════════════════════

# GET /api/personas → Retorna lista de personas en JSON
# El navegador o Postman puede llamar esto directamente
@app.get("/api/personas", tags=["API"])
def api_ver_personas(session: SessionDep):
    return ver_personas(session)   # FastAPI convierte automáticamente a JSON


# POST /api/personas → Crea persona desde JSON (no formulario)
# El body debe ser: {"nombre": "Ana", "edad": 25, "ciudad": "Bogotá"}
@app.post("/api/personas", tags=["API"])
def api_crear_persona(datos: PersonaBase, session: SessionDep):
    return crear_persona(datos, session)


# GET /api/personas/{id} → Retorna una persona por ID
# {id} es un parámetro de ruta. Ej: /api/personas/3 → busca id=3
@app.get("/api/personas/{id}", tags=["API"])
def api_una_persona(id: int, session: SessionDep):
    persona = buscar_por_id(id, session)
    if not persona:
        # HTTPException → FastAPI devuelve un error HTTP con código 404
        raise HTTPException(status_code=404, detail=f"Persona {id} no encontrada")
    return persona


# PATCH /api/personas/{id} → Edita campos de una persona
# PATCH = actualización parcial (solo los campos que se envíen)
# El JavaScript lo llama con: fetch('/api/personas/1', {method: 'PATCH', body: ...})
@app.patch("/api/personas/{id}", tags=["API"])
def api_editar_persona(id: int, datos: PersonaUpdate, session: SessionDep):
    actualizada = editar_persona(id, datos, session)
    if not actualizada:
        raise HTTPException(status_code=404, detail=f"Persona {id} no encontrada")
    return actualizada


# DELETE /api/personas/{id} → Desactiva una persona (soft delete)
# El JavaScript lo llama con: fetch('/api/personas/1', {method: 'DELETE'})
@app.delete("/api/personas/{id}", tags=["API"])
def api_desactivar_persona(id: int, session: SessionDep):
    persona = buscar_por_id(id, session)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona {id} no encontrada")
    if persona.estado == "inactivo":
        raise HTTPException(status_code=409, detail="La persona ya estaba inactiva")
    return desactivar_persona(id, session)


# POST /api/personas/{id}/imagen → Sube una imagen para la persona
# El JavaScript lo llama con FormData (para enviar archivos)
@app.post("/api/personas/{id}/imagen", tags=["API"])
async def api_imagen_persona(
    id:     int,
    session: SessionDep,
    imagen: UploadFile = File(...)
):
    persona = buscar_por_id(id, session)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    # Sube la imagen a Supabase Storage y obtén su URL pública
    contenido = await imagen.read()
    url = subir_imagen_a_supabase(
        contenido, imagen.filename, imagen.content_type
    )

    # Actualiza la URL en la BD y retorna la persona actualizada
    return actualizar_imagen(id, url, session)