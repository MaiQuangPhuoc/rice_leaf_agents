# test_retriever.py
import logging
import sys, os
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.clients.embedding import embeddings_qa
from src.configs import env_config
from retrievers2 import VectorStoreRetriever

retriever = VectorStoreRetriever(
    url=env_config.qdrant_url,
    api_key=env_config.qdrant_api_key,
    embeddings=embeddings_qa,
    collection_name="documents",
    top_k=10,
)

query = "bệnh khô vằn lây lan như thế nào và các triệu chứng của bệnh khô vằn trên lá lúa?"

 

docs = retriever.search_and_filter_rerank(
    query=query,
    disease="BỆNH KHÔ VẰN",
    keywords=["lây lan", "triệu chứng", "vết bệnh"],
    min_results=1,
    filter_top_k=7,
    rerank_top_k=3
)

print("\n===== RERANKED RESULTS =====")

for doc in docs:
    print(f"[{doc.metadata['disease']}] - {doc.metadata['topic']}")
    print(doc.page_content[:200])
    print("---")

# print("===== SEMANTIC =====")
# for doc, score in retriever._dense_store.similarity_search_with_score(query, k=10):
#     print(f"Score: {score:.4f} | [{doc.metadata['disease']}] - {doc.metadata['topic']}")

# print("\n===== TEXT =====")
# for doc, score in retriever._sparse_store.similarity_search_with_score(query, k=10):
#     print(f"Score: {score:.4f} | [{doc.metadata['disease']}] - {doc.metadata['topic']}")

# print("\n===== HYBRID =====")
# for doc, score in retriever._hybrid_store.similarity_search_with_score(query, k=10):
#     print(f"Score: {score:.4f} | [{doc.metadata['disease']}] - {doc.metadata['topic']}")


# print("\n===== FILTERED RESULTS =====")

# for doc in docs:
#     print(f"[{doc.metadata['disease']}] - {doc.metadata['topic']}\n")
    # print(doc.page_content[:200])
    # print("---")

