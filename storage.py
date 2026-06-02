# ─────────────────────────────────────────────────────────────
# storage.py → Conexión con Supabase Storage (bucket de imágenes)
#
# Este archivo hace UNA sola cosa: subir una imagen al bucket de
# Supabase y devolver la URL pública para guardarla en la BD.
#
# Antes las imágenes se guardaban en la carpeta local static/imgs.
# Ahora viven en Supabase, así no se pierden al desplegar en Render
# (en Render el disco es temporal y se borra en cada despliegue).
# ─────────────────────────────────────────────────────────────

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv                  # lee el archivo .env
from supabase import create_client, Client      # cliente oficial de Supabase

load_dotenv()  # carga SUPABASE_URL, SUPABASE_KEY y SUPABASE_BUCKET desde .env

SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

# Si falta alguna variable avisamos claro al arrancar, en vez de
# fallar con un error confuso la primera vez que alguien suba una foto.
if not (SUPABASE_URL and SUPABASE_KEY and SUPABASE_BUCKET):
    raise RuntimeError(
        "Faltan variables de Supabase en el .env. "
        "Necesitas: SUPABASE_URL, SUPABASE_KEY y SUPABASE_BUCKET."
    )

# Cliente de Supabase. Se crea UNA sola vez cuando arranca el servidor.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def subir_imagen_a_supabase(
    contenido: bytes,
    nombre_archivo: str,
    content_type: str | None = None,
) -> str:
    """
    Sube una imagen al bucket de Supabase y devuelve su URL pública.

    Parámetros
    ----------
    contenido      : los bytes del archivo (se obtienen con: await imagen.read())
    nombre_archivo : el nombre original, solo para sacar la extensión (.jpg, .png)
    content_type   : el tipo MIME del archivo (imagen.content_type)

    Devuelve
    --------
    str : la URL pública de la imagen, lista para guardar en la BD.
    """
    # 1. Generamos un nombre ÚNICO para que dos fotos nunca se pisen.
    #    Ejemplo de ruta dentro del bucket: personas/3f9a2c...e1.jpg
    extension = Path(nombre_archivo).suffix.lower() or ".bin"
    ruta_en_bucket = f"personas/{uuid.uuid4().hex}{extension}"

    # 2. Subimos los bytes al bucket.
    #    file_options son cabeceras HTTP:
    #      - content-type → para que el navegador muestre la imagen bien
    #      - upsert       → si la ruta ya existe, la reemplaza en vez de fallar
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=ruta_en_bucket,
        file=contenido,
        file_options={
            "content-type": content_type or "application/octet-stream",
            "upsert": "true",
        },
    )

    # 3. Pedimos la URL pública del archivo recién subido.
    #    OJO: el bucket debe estar marcado como PÚBLICO en Supabase para
    #    que esta URL se abra en el navegador. get_public_url añade un "?"
    #    al final, así que lo quitamos para dejar la URL limpia.
    url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(ruta_en_bucket)
    return url.rstrip("?")