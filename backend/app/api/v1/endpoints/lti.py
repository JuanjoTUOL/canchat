from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
import logging
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/login")
def lti_login():
    """Punto de entrada para el flujo de autenticación OIDC."""
    return {"msg": "Iniciando handshake OIDC con Moodle..."}

@router.post("/launch")
async def lti_launch(
    request: Request,
    user_id: str = Form(None, alias="user_id"),
    course_id: str = Form(None, alias="context_id"),
    roles: str = Form(None, alias="roles")
):
    """
    Recibe el POST de Moodle (LTI Launch).
    Extrae la identidad del alumno y el curso.
    """
    #Log para tu memoria (demuestra que recibes datos)
    print(f"--- LTI LAUNCH DETECTADO ---")
    print(f"Usuario Moodle: {user_id}")
    print(f"Curso detectado: {course_id}")
    print(f"Roles: {roles}")

    #Usamos la URL del servidor dinámicamente y pasamos el user_id
    url_frontend = f"{settings.FRONTEND_URL}/?course_id={course_id}&user_id={user_id}"
    
    return RedirectResponse(url=url_frontend, status_code=303)