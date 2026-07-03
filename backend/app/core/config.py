from typing import Optional 
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TFG RAG"
    API_V1_STR: str = "/api/v1"
    
    FRONTEND_URL: str = "http://localhost:8501"

    #LLM Config 
    LLM_PROVIDER: str = "ollama" #Le damos un valor por defecto
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL_NAME: str = "llama3"
    LLM_API_KEY: Optional[str] = None #Opcional
    
    #Embedding Config
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_BASE_URL: Optional[str] = None #Opcional
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    #Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "moodle_materials"

    #Security (LTI)
    LTI_PRIVATE_KEY_PATH: str = "certs/private.key"
    LTI_PUBLIC_JWK_URL: str = "http://localhost:8000/lti/jwks"
    
    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()