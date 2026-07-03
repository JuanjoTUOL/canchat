#CANCHAT — Asistente académico basado en RAG integrado con Moodle

Trabajo de Fin de Grado — Universidad de Cantabria  
Autor: Juan José Turcios Olalla  

##Descripción

Asistente académico que permite a los estudiantes consultar los apuntes de sus asignaturas en lenguaje natural. Las respuestas se generan exclusivamente a partir de los documentos subidos por el profesor, evitando alucinaciones mediante la técnica RAG. Se integra con Moodle via LTI y ejecuta todos los modelos de IA de forma local.

##Requisitos

- Python 3.11+
- Docker
- Ollama (desarrollo local)
- Token de HuggingFace (producción)

##Instalación local


git clone https://github.com/JuanjoTUOL/canchat.git
cd canchat
cp .env.example .env

#Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

#Frontend (otra terminal)
cd frontend
pip install -r requisitos.txt
streamlit run app.py
```

Qdrant en Docker:
```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

##Despliegue en producción (Triton)

```bash
docker compose -f docker-compose.triton.yml up -d --build
```

##Nota sobre Moodle

La imagen `public.ecr.aws/bitnami/moodle:4.1` dejó de estar disponible públicamente en febrero de 2026. Para usarla es necesario tenerla en caché local y cargarla con `docker load`. El resto del sistema funciona de forma independiente sin Moodle.
