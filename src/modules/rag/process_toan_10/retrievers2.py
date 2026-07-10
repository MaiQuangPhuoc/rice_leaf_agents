# src/modules/rag/retrievers.py
import os
os.environ["FASTEMBED_CACHE_PATH"] = r"C:\Users\Phuoc\fastembed_cache"
import logging
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class VectorStoreRetriever:
    def __init__(
        self,
        url: str,
        api_key: str,
        embeddings: Embeddings,
        collection_name: str = "documents",
        top_k: int = 10,
        reranker_model: str = "BAAI/bge-reranker-base"
    ):
        self._client = QdrantClient(
            url=url,
            api_key=api_key,
            check_compatibility=False,
        )

        # Semantic search (dense only)
        self._dense_store = QdrantVectorStore(
            client=self._client,
            collection_name=collection_name,
            embedding=embeddings,
            vector_name="dense",
            retrieval_mode=RetrievalMode.DENSE,
        )

        # Text search (sparse only)
        self._sparse_store = QdrantVectorStore(
            client=self._client,
            collection_name=collection_name,
            embedding=embeddings,
            vector_name="dense",
            sparse_vector_name="sparse",
            retrieval_mode=RetrievalMode.SPARSE,
            sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
        )

        # Hybrid search
        self._hybrid_store = QdrantVectorStore(
            client=self._client,
            collection_name=collection_name,
            embedding=embeddings,
            vector_name="dense",
            sparse_vector_name="sparse",
            retrieval_mode=RetrievalMode.HYBRID,
            sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
        )

        self.top_k = top_k

        # Reranker
        self._reranker = CrossEncoder(reranker_model)
        logger.info(f"Reranker loaded: {reranker_model}")

        logger.info(f"VectorStoreRetriever initialized | collection: {collection_name} | top_k: {top_k}")


    

    def semantic_search(self, query: str) -> list[Document]:
        """Tìm kiếm theo ngữ nghĩa (dense vector)."""
        results = self._dense_store.similarity_search(query, k=self.top_k)
        # logger.info(f"Semantic search: {len(results)} kết quả")
        print(f" ========== semantic search : {len(results)} ========== ")
        
        return results

    def text_search(self, query: str) -> list[Document]:
        """Tìm kiếm theo từ khóa (sparse - BM25)."""
        results = self._sparse_store.similarity_search(query, k=self.top_k)
        # logger.info(f"Text search: {len(results)} kết quả")
        print(f" ========== Text search : {len(results)} ========== ")

        return results

    def hybrid_search(self, query: str) -> list[Document]:
        """Kết hợp semantic + text search."""
        results = self._hybrid_store.similarity_search(query, k=self.top_k)
        # logger.info(f" ******************* Hybrid search: {len(results)} kết quả")
        print(f" ========== hibird search : {len(results)} ========== ")

        return results

    def rerank(self, query: str, docs: list, top_k: int = 3) -> list[Document]:
        """Rerank docs bằng cross-encoder, chỉ giữ top_k chính xác nhất."""
        if not docs:
            return []

        pairs = [[query, doc.page_content] for doc in docs]
        scores = self._reranker.predict(pairs)

        ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)

        # logger.info(f"Rerank scores: {[round(float(s), 4) for s, _ in ranked]}")
        print(f" ========== Rerank scores: {[round(float(s), 4) for s, _ in ranked]} ========== ")

        return [doc for _, doc in ranked[:top_k]]
    
