/* ============================================================
   app.js → JavaScript GLOBAL del proyecto.

   Aquí van las funciones genéricas que comparten TODAS las páginas:
     - abrir / cerrar las ventanas emergentes (modales)
     - guardar la edición de una persona  → PATCH a la API
     - subir la foto de una persona        → POST a la API

   Las funciones específicas de personas.html (toggleFormulario,
   abrirModalEditar, abrirModalFoto, eliminarPersona) están en el
   bloque <script> de esa página, porque usan datos de Jinja2
   como {{ p.id }}. Este archivo se carga ANTES desde base.html.
   ============================================================ */

/*
   idActual guarda el ID de la persona que se está editando o a la que
   se le va a cambiar la foto.

   Lo ASIGNAN  abrirModalEditar() y abrirModalFoto()  (en personas.html)
   justo antes de abrir el modal, y lo LEEN  guardarEdicion() y
   subirFoto()  para saber a quién hay que actualizar en la API.
*/
let idActual = null;


// ════════════════════════════════════════════════════════════
//  MODALES (ventanas emergentes)
// ════════════════════════════════════════════════════════════

// Muestra el fondo oscuro y el modal indicado por su id.
function abrirModal(idModal) {
    document.getElementById("modal-overlay").style.display = "block";
    document.getElementById(idModal).style.display = "block";
}

// Oculta un modal concreto y el fondo oscuro.
function cerrarModal(idModal) {
    document.getElementById(idModal).style.display = "none";
    document.getElementById("modal-overlay").style.display = "none";
}

// Oculta TODOS los modales y el fondo oscuro.
// Se llama al hacer clic en el fondo oscuro (#modal-overlay).
function cerrarTodosModales() {
    document.getElementById("modal-editar").style.display = "none";
    document.getElementById("modal-foto").style.display = "none";
    document.getElementById("modal-overlay").style.display = "none";
}


// ════════════════════════════════════════════════════════════
//  ACCIONES QUE HABLAN CON LA API (fetch)
// ════════════════════════════════════════════════════════════

/*
   Convierte el error que devuelve FastAPI en un texto legible.
   FastAPI manda "detail" de dos formas:
     - como texto      → ej: "Persona 5 no encontrada"
     - como lista       → cuando falla la validación de Pydantic
   Esta función cubre los dos casos para no mostrar "[object Object]".
*/
function extraerError(data) {
    if (!data || !data.detail) return "Ocurrió un error inesperado.";
    if (typeof data.detail === "string") return data.detail;
    return data.detail.map(e => e.msg).join(" | ");
}

// Guarda los cambios del modal de editar → PATCH /api/personas/{id}
async function guardarEdicion() {
    // Leemos los valores que el usuario escribió en el modal.
    // edad se convierte a número porque en el HTML llega como texto.
    const datos = {
        nombre: document.getElementById("edit-nombre").value,
        edad:   parseInt(document.getElementById("edit-edad").value, 10),
        ciudad: document.getElementById("edit-ciudad").value
    };

    const respuesta = await fetch(`/api/personas/${idActual}`, {
        method:  "PATCH",
        headers: { "Content-Type": "application/json" }, // enviamos JSON
        body:    JSON.stringify(datos)                   // objeto → texto JSON
    });

    if (respuesta.ok) {
        location.reload();  // recarga la página para ver los cambios
    } else {
        const error = await respuesta.json();
        alert("Error: " + extraerError(error));
    }
}

// Sube la foto elegida en el modal → POST /api/personas/{id}/imagen
async function subirFoto() {
    const input = document.getElementById("input-foto");

    // Validamos que el usuario haya seleccionado un archivo.
    if (!input.files || input.files.length === 0) {
        alert("Selecciona una imagen primero.");
        return;
    }

    /*
       Para enviar ARCHIVOS no se usa JSON, se usa FormData.
       La clave "imagen" DEBE coincidir con el parámetro del endpoint:
         async def api_imagen_persona(..., imagen: UploadFile = File(...))
    */
    const formData = new FormData();
    formData.append("imagen", input.files[0]);

    const respuesta = await fetch(`/api/personas/${idActual}/imagen`, {
        method: "POST",
        body:   formData
        // OJO: NO ponemos "Content-Type" a mano. Con FormData el navegador
        // lo añade solo, junto al "boundary" que el servidor necesita.
    });

    if (respuesta.ok) {
        location.reload();
    } else {
        const error = await respuesta.json();
        alert("Error: " + extraerError(error));
    }
}