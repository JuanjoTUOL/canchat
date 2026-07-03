import logging
import hashlib
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = settings.QDRANT_COLLECTION

        #Compruebo si uso Embeddings locales o servidor TEI
        if settings.EMBEDDING_PROVIDER == "tei":
            # En ese caso, usamos la API de TEI compatible con protocolo OpenAI
            self.embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL_NAME,
                base_url=settings.EMBEDDING_BASE_URL,
                api_key="fake-key"  # TEI no requiere clave pero el cliente la pide
            )
            #Este es el tamaño típico de modelos profesionales como BGE-M3
            self.vector_size = 1024
        else:
            #Si es mi PC 
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_NAME
            )
            self.vector_size = 384  # Tamaño de all-MiniLM-L6-v2

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        self._ensure_collection_exists()

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )

    def _ensure_collection_exists(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    async def ingest_text(self, text: str, metadata: dict):
        chunks = self.text_splitter.split_text(text)

        #Generamos IDs únicos para cada trozo
        ids = [hashlib.md5(f"{chunk}-{metadata.get('course_id')}".encode()).hexdigest() for chunk in chunks]
        metadatas = [metadata for _ in chunks]

        #Comprobamos cuantos de estos IDs ya existen en Qdrant antes de insertar
        existing = self.client.retrieve(collection_name=self.collection_name, ids=ids, with_payload=False)
        num_existentes = len(existing)

        #TEI limita el tamaño de batch a 32 textos por petición de embedding, así que troceamos la ingesta en lotes para no superar ese límite.
        batch_size = 32
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            await self.vector_store.aadd_texts(texts=batch_chunks, metadatas=batch_metadatas, ids=batch_ids)

        total = len(chunks)
        omitidos = num_existentes
        insertados = total - omitidos

        logger.info(f"{metadata.get('filename')}: {insertados} nuevos, {omitidos} omitidos por duplicados (total {total})")
        return {"total": total, "insertados": insertados, "omitidos": omitidos}

    async def search(self, query: str, course_id: str, limit: int = 12):
        #Filtro para Qdrant para aislamiento
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.course_id",
                    match=models.MatchValue(value=course_id)
                )
            ]
        )

        return await self.vector_store.asimilarity_search(
            query=query,
            k=limit,
            filter=filter_condition
        )
