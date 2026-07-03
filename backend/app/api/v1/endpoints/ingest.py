from typing import List
from fastapi import APIRouter, UploadFile, File, Form
from app.utils.pdf_loader import extract_text_from_pdf
from app.services.rag.vector_store import VectorService

router = APIRouter()
vector_service = VectorService()

@router.post("/")
async def ingest_documents(
    files: List[UploadFile] = File(...),
    course_id: str = Form(...)
):
    resultados_exito = []
    resultados_error = []  # Lista de archivos correctos y malos

    for file in files:
        if not file.filename.endswith('.pdf'):
            resultados_error.append({"archivo": file.filename, "error": "Formato no válido (solo PDF)"})
            continue

        try:
            # Extraemos texto
            text = await extract_text_from_pdf(file)

            if not text.strip():
                resultados_error.append({"archivo": file.filename, "error": "El PDF no contiene texto extraíble"})
                continue

            # Guardamos con metadatos
            metadata = {
                "filename": file.filename,
                "course_id": course_id
            }
            resultado = await vector_service.ingest_text(text, metadata)

            # Registramos éxito, con desglose de nuevos vs omitidos
            resultados_exito.append({
                "archivo": file.filename,
                "chunks_creados": resultado["insertados"],
                "chunks_omitidos_duplicados": resultado["omitidos"],
                "chunks_totales": resultado["total"]
            })

        except Exception as e:
            # Registramos un error, pero se continua
            print(f"Error procesando {file.filename}: {str(e)}")
            resultados_error.append({"archivo": file.filename, "error": str(e)})

    # Miramos el estado final para que el frontend sepa qué icono mostrar
    if not resultados_error:
        estado = "success"
    elif not resultados_exito:
        estado = "error"
    else:
        estado = "partial_success"

    return {
        "status": estado,
        "message": f"Procesamiento finalizado: {len(resultados_exito)} correctos, {len(resultados_error)} fallidos.",
        "detalles": {
            "course_id": course_id,
            "exitos": resultados_exito,
            "errores": resultados_error
        }
    }
