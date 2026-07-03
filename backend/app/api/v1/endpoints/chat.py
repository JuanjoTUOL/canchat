from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag.agent import rag_agent 

router = APIRouter()

#Estructura de las request
class ChatRequest(BaseModel):
    message: str 
    course_id: str #identificador curso
    user_id: str  #identificador alumno

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    try:
        #Generamos un hilo de memoria dinámico y aislado, Formato: curso_usuario
        session_id = f"{request.course_id}_{request.user_id}"
        config = {"configurable": {"thread_id": session_id}}
        
        inputs = {
            "question": request.message, 
            "course_id": request.course_id,
            "context": [],
            "answer": "",
            "history": []
        }
        
        #El endpoint invoca al agente
        result = await rag_agent.ainvoke(inputs, config=config)
        
        return {
            "answer": result["answer"],
            "sources": result.get("context", [])
        }
    except Exception as e:
        print(f"Error en el chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))