from fastapi import APIRouter
from app.api.v1.endpoints import chat, ingest, lti

api_router = APIRouter()

#Aqui conectamos todo
api_router.include_router(lti.router, prefix="/lti", tags=["lti"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])