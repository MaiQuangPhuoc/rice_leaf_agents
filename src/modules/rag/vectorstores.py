import logging
from typing import List, Optional

from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class VectorStoreManager:
    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        prefer_grpc: bool = False,
    ):
        self.url = url
        self.api_key = api_key
        self.prefer_grpc = prefer_grpc
        self._client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            prefer_grpc=self.prefer_grpc,
            check_compatibility=False,
        )
        logger.info(f"VectorStoreManager initialized with URL: {url}")

    def create_vector_store(
        self,
        documents: List[Document],
        embeddings: Embeddings,
        collection_name: str = "test2",
    ) -> QdrantVectorStore:

        if not documents:
            raise ValueError("Documents list cannot be empty")
        if not embeddings:
            raise ValueError("Embeddings model is required")

        try:
            vector_store = QdrantVectorStore(
                client=self._client,
                collection_name=collection_name,
                embedding=embeddings,
                retrieval_mode=RetrievalMode.HYBRID,   # dense + sparse
                sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),  # sparse
            )

            vector_store.add_documents(documents)

            logger.info(f"✅ Upserted {len(documents)} documents vào collection '{collection_name}'")
            return vector_store

        except Exception as e:
            logger.error(f"❌ Failed to upsert: {str(e)}")
            raise

    def get_client(self) -> QdrantClient:
        return self._client