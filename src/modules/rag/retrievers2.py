# # src/modules/rag/retrievers.py
# import os
# os.environ["FASTEMBED_CACHE_PATH"] = r"C:\Users\Phuoc\fastembed_cache"
# import logging
# from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
# from langchain_core.embeddings import Embeddings
# from langchain_core.documents import Document
# from qdrant_client import QdrantClient

# from sentence_transformers import CrossEncoder

# logger = logging.getLogger(__name__)


# class VectorStoreRetriever:
#     def __init__(
#         self,
#         url: str,
#         api_key: str,
#         embeddings: Embeddings,
#         collection_name: str = "documents",
#         top_k: int = 10,
#         reranker_model: str = "BAAI/bge-reranker-base"
#     ):
#         self._client = QdrantClient(
#             url=url,
#             api_key=api_key,
#             check_compatibility=False,
#         )

#         # Semantic search (dense only)
#         self._dense_store = QdrantVectorStore(
#             client=self._client,
#             collection_name=collection_name,
#             embedding=embeddings,
#             vector_name="dense",
#             retrieval_mode=RetrievalMode.DENSE,
#         )

#         # Text search (sparse only)
#         self._sparse_store = QdrantVectorStore(
#             client=self._client,
#             collection_name=collection_name,
#             embedding=embeddings,
#             vector_name="dense",
#             sparse_vector_name="sparse",
#             retrieval_mode=RetrievalMode.SPARSE,
#             sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
#         )

#         # Hybrid search
#         self._hybrid_store = QdrantVectorStore(
#             client=self._client,
#             collection_name=collection_name,
#             embedding=embeddings,
#             vector_name="dense",
#             sparse_vector_name="sparse",
#             retrieval_mode=RetrievalMode.HYBRID,
#             sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
#         )

#         self.top_k = top_k

#         # Reranker
#         self._reranker = CrossEncoder(reranker_model)
#         logger.info(f"Reranker loaded: {reranker_model}")

#         logger.info(f"VectorStoreRetriever initialized | collection: {collection_name} | top_k: {top_k}")


    

#     def semantic_search(self, query: str) -> list[Document]:
#         """Tìm kiếm theo ngữ nghĩa (dense vector)."""
#         results = self._dense_store.similarity_search(query, k=self.top_k)
#         # logger.info(f"Semantic search: {len(results)} kết quả")
#         print(f" ========== semantic search : {len(results)} ========== ")
        
#         return results

#     def text_search(self, query: str) -> list[Document]:
#         """Tìm kiếm theo từ khóa (sparse - BM25)."""
#         results = self._sparse_store.similarity_search(query, k=self.top_k)
#         # logger.info(f"Text search: {len(results)} kết quả")
#         print(f" ========== Text search : {len(results)} ========== ")

#         return results

#     def hybrid_search(self, query: str) -> list[Document]:
#         """Kết hợp semantic + text search."""
#         results = self._hybrid_store.similarity_search(query, k=self.top_k)
#         # logger.info(f" ******************* Hybrid search: {len(results)} kết quả")
#         print(f" ========== hibird search : {len(results)} ========== ")

#         return results

#     def rerank(self, query: str, docs: list, top_k: int = 3) -> list[Document]:
#         """Rerank docs bằng cross-encoder, chỉ giữ top_k chính xác nhất."""
#         if not docs:
#             return []

#         pairs = [[query, doc.page_content] for doc in docs]
#         scores = self._reranker.predict(pairs)

#         ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)

#         # logger.info(f"Rerank scores: {[round(float(s), 4) for s, _ in ranked]}")
#         print(f" ========== Rerank scores: {[round(float(s), 4) for s, _ in ranked]} ========== ")

#         return [doc for _, doc in ranked[:top_k]]
    
#     # retrievers2.py - thêm method vào class VectorStoreRetriever

#     def search_and_filter(
#         self,
#         query: str,
#         disease: str = None,
#         topic: str = None,
#         keywords: list = None,
#         min_results: int = 2,
#         top_k: int = 6,
#     ) -> list[Document]:
        
#         # Bước 1: Retrieve
#         results = self.hybrid_search(query)
#         if not results:
#             return []

#         # Bước 2: Filter disease
#         if disease:
#             filtered = [doc for doc in results if doc.metadata.get("disease") == disease]
#             results = filtered if len(filtered) >= min_results else results

#         # Bước 3: Filter keywords
#         if keywords:
#             filtered = [
#                 doc for doc in results
#                 if any(kw in doc.metadata.get("keywords", []) for kw in keywords)
#             ]
#             results = filtered if len(filtered) >= min_results else results

#         # Bước 4: Filter topic
#         if topic:
#             filtered = [doc for doc in results if doc.metadata.get("topic") == topic]
#             results = filtered if len(filtered) >= min_results else results

#         # Bước 5: Lấy top_k tốt nhất
#         results = results[:top_k]

#         # logger.info(f" ***************** search_and_filter: {len(results)} kết quả sau filter")
#         return results
    
#     def search_and_filter_rerank(
#         self,
#         query: str,
#         disease: str = None,
#         topic: str = None,
#         keywords: list = None,
#         min_results: int = 2,
#         filter_top_k: int = 6,   # sau filter lấy 6
#         rerank_top_k: int = 3,   # sau rerank lấy 3
#     ) -> list[Document]:
#         """Retrieve (10) → filter (6) → rerank (3)."""

#         # Bước 1: Hybrid search top 10
#         results = self.hybrid_search(query)  # top_k=10 từ __init__
#         if not results:
#             return []

#         # Bước 2: Filter metadata
#         if disease:
#             disease_list = disease if isinstance(disease, list) else [disease]
#             filtered = [doc for doc in results if doc.metadata.get("disease") in disease_list]
#             results = filtered if len(filtered) >= min_results else results

#         results = results[:filter_top_k]

#         for doc in results:
#             print(f"\n==========\nTrước rerank: [{doc.metadata['disease']}]")
 

            

#         # logger.info(f" ***************** Sau filter: {len(results)} docs")
#         print(f" ========== Sau fillter : {len(results)} ========== ")


#         # Bước 3: Rerank top rerank_top_k
#         results = self.rerank(query, results, top_k=rerank_top_k)
#         # logger.info(f" ***************** Sau rerank: {len(results)} docs")
#         print(f" ========== sau re_rank : {len(results)} ========== ")
#         for doc in results:
#             print(f"\n==========\Sau rerank: [{doc.metadata['disease']}]")


#         return results