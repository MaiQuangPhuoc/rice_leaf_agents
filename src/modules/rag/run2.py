from loaders import DocumentLoader
from processors import DocumentProcessor
import re
from langchain_core.documents import Document
from vectorstores import VectorStoreManager
from retrievers import VectorStoreRetriever

import sys , os 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".." ,"..")))
from src.clients.embedding import embeddings
from src.configs import env_config

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.schema import Document

# Embedding model
embeddings = HuggingFaceEmbeddings(model_name="dangvantuan/vietnamese-embedding")

# Tạo documents mẫu
docs = [
    Document(page_content="Tôi yêu toán học", metadata={"id": 1}),
    Document(page_content="Học AI với Python", metadata={"id": 2}),
]

# Push vào Qdrant
qdrant = Qdrant.from_documents(
    documents=docs,
    embedding=embeddings,
    url="https://<CLUSTER_URL>.qdrant.io",
    api_key="<API_KEY>",
    collection_name="documents_dangvantuan",
)

print("Đã insert", len(docs), "vectors")
