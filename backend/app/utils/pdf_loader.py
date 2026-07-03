import io
from pypdf import PdfReader
from fastapi import UploadFile

async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Lee el contenido de un archivo PDF subido y extrae todo su texto.
    """
    # 1. Leemos los bytes del archivo que viene de FastAPI
    content = await file.read()
    
    # 2. Lo metemos en un "archivo virtual" en memoria (BytesIO)
    pdf_file = io.BytesIO(content)
    
    # 3. Usamos PdfReader para extraer el texto
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
            
    
    return text