# CANCHAT — Asistente académico basado en RAG integrado con Moodle

Trabajo de Fin de Grado — Universidad de Cantabria  
Autor: Juan José Turcios Olalla  
Director: Esteban Stafford Fernández

## Descripción

Sistema de asistente académico que permite a los estudiantes consultar los materiales de sus asignaturas en lenguaje natural, obteniendo respuestas fundamentadas exclusivamente en los documentos subidos por el profesor. Se integra con Moodle mediante el estándar LTI, ejecutando todos los modelos de IA de forma local sin depender de servicios externos de pago.

## Arquitectura

```
Moodle (LMS) ──LTI──► Backend (FastAPI) ──► Agente LangGraph
                              │                      │
                              ▼                      ▼
                         /ingest              Qdrant (vectores)
                              │                      │
                              ▼                      ▼
                         Streamlit              LLM (vLLM/Ollama)
```

## Stack tecnológico

- **Backend**: FastAPI + LangGraph + Qdrant
- **LLM**: Ollama (desarrollo) / vLLM con Llama-3.1-8B-Instruct (producción)
- **Embeddings**: all-MiniLM-L6-v2 (desarrollo) / BGE-M3 via TEI (producción)
- **Frontend**: Streamlit
- **Integración**: LTI 1.1 con Moodle 4.1

## Instalación y uso

### Desarrollo local

1. Copia el archivo de variables de entorno:
```bash
cp .env.example .env
# Edita .env con tus valores
```

2. Instala las dependencias del backend:
```bash
cd backend
pip install -r requirements.txt
```

3. Instala las dependencias del frontend:
```bash
cd frontend
pip install -r requisitos.txt
```

4. Arranca Qdrant en Docker:
```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

5. Arranca Ollama con el modelo:
```bash
ollama serve
ollama pull llama3.1:8b
```

6. Arranca el backend:
```bash
cd backend
uvicorn app.main:app --reload
```

7. Arranca el frontend:
```bash
cd frontend
streamlit run app.py
```

### Producción (servidor Triton)

```bash
docker compose -f docker-compose.triton.yml up -d --build
```

## Estructura del proyecto

```
canchat/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── chat.py       # Endpoint de consulta
│   │   │   │   ├── ingest.py     # Endpoint de ingesta de PDFs
│   │   │   │   └── lti.py        # Endpoint de lanzamiento LTI
│   │   │   └── router.py
│   │   ├── core/config.py        # Configuración por variables de entorno
│   │   ├── services/rag/
│   │   │   ├── agent.py          # Agente LangGraph (retrieve + generate)
│   │   │   └── vector_store.py   # Comunicación con Qdrant
│   │   ├── utils/pdf_loader.py   # Extracción de texto de PDFs
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py                    # Interfaz Streamlit
│   ├── Dockerfile
│   └── requisitos.txt
├── docker-compose.triton.yml     # Despliegue en producción
├── .env.example                  # Plantilla de variables de entorno
└── .gitignore
```
