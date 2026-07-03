from typing import List, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.services.rag.vector_store import VectorService

# Inicializamos las herramientas
vector_service = VectorService()

# Compruebo si estoy en mi entorno de desarrollo o en el servidor (Triton)
if settings.LLM_PROVIDER == "vllm":
    llm = ChatOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL_NAME,
        temperature=0
    )
else:
    llm = ChatOllama(
        model=settings.LLM_MODEL_NAME,
        base_url=settings.LLM_BASE_URL,
        temperature=0  # Temperatura 0 para maximizar el determinismo en las respuestas
    )

# Persistencia en memoria para el grafo de LangGraph
memory = MemorySaver()

# Definimos el esquema del Estado (State) del agente
class AgentState(TypedDict):
    question: str
    context: List[str]
    answer: str
    course_id: str
    history: List[BaseMessage]

# DEFINICIÓN DE NODOS DEL GRAFO

async def retrieve_node(state: AgentState):
    """Nodo encargado de la consulta a la base de datos vectorial (Qdrant)."""
    results = await vector_service.search(query=state["question"], course_id=state["course_id"])
    unique_contexts = list(dict.fromkeys([doc.page_content for doc in results]))
    return {"context": unique_contexts}

async def generate_node(state: AgentState):
    """Nodo encargado de la inferencia del LLM con el contexto inyectado."""
    chat_history_str = ""
    for msg in state.get("history", []):
        role = "Estudiante" if isinstance(msg, HumanMessage) else "Asistente"
        chat_history_str += f"{role}: {msg.content}\n"

    context_str = "\n\n---\n\n".join(state['context'])

    # El prompt pide al modelo que exprese su interpretación antes de la respuesta final,
    # marcada con la etiqueta RESPUESTA:. El backend descarta todo lo anterior a esa marca,
    # de forma que el razonamiento interno no llega al alumno.
    # Esto mejora la tolerancia a erratas sin sacrificar la fidelidad al contexto.
    system_prompt = f"""Eres un asistente académico que responde ÚNICAMENTE basándose en el CONTEXTO DEL PDF de abajo.

La pregunta del estudiante puede tener erratas o estar mal escrita (por ejemplo "uin" significa "un", "ociuklto" significa "oculto"); interprétala correctamente antes de responder.

Antes de dar tu respuesta final, escribe brevemente qué concepto crees que te están preguntando realmente.

Después, en una nueva línea, escribe exactamente "RESPUESTA:" seguido de tu respuesta final, siguiendo estas reglas:
- Si el concepto aparece en el CONTEXTO DEL PDF (aunque sea mencionado brevemente), explícalo usando solo esa información.
- Si el concepto NO aparece en el contexto de ninguna forma, escribe exactamente: "No dispongo de esa información en los apuntes." No uses conocimiento general bajo ningún concepto, ni para preguntas que parezcan de cultura general básica (personas famosas, capitales, fechas históricas, etc.).

CONTEXTO DEL PDF:
{context_str}

HISTORIAL DE LA CONVERSACIÓN:
{chat_history_str}"""

    # Estructuración del payload de mensajes para la API del LLM
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state['question'])
    ]

    # Llamada asíncrona (ainvoke) para no bloquear el Event Loop de FastAPI
    response = await llm.ainvoke(messages)

    # Post-procesado: nos quedamos solo con la parte tras "RESPUESTA:",
    # ocultando el razonamiento intermedio del modelo al alumno.
    raw_answer = response.content
    if "RESPUESTA:" in raw_answer:
        final_answer = raw_answer.split("RESPUESTA:", 1)[1].strip()
    else:
        final_answer = raw_answer.strip()

    # Actualización del historial de la sesión
    new_history = list(state.get("history", [])) + [
        HumanMessage(content=state["question"]),
        AIMessage(content=final_answer)
    ]

    return {"answer": final_answer, "history": new_history}

# CONSTRUCCIÓN DEL GRAFO DE EJECUCIÓN

workflow = StateGraph(AgentState)

# Añadimos los nodos
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

# Definimos el flujo de ejecución (Edges)
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# Compilamos el grafo pasando el sistema de persistencia de memoria
rag_agent = workflow.compile(checkpointer=memory)
