"""
qdrant_indexer.py
Upload all_chunks (từ chunker.py) lên Qdrant collection.
"""

from __future__ import annotations
import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..","..","..")))
import uuid
from pathlib import Path
from typing import Any
from src.configs import env_config

from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
)

# print("pl")
from chunker import split_chapters, make_chapter_chunk, make_lesson_chunks, make_section_chunks, norm


# ── Config ────────────────────────────────────────────────────────────────────

COLLECTION_NAME = "doc_toan_10_1"
EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"
BATCH_SIZE      = 64          # số point upload mỗi lần


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_chunks(filepath: str) -> list[dict]:
    """Chạy toàn bộ pipeline chunking và normalize text."""
    chapters   = split_chapters(filepath)
    all_chunks: list[dict] = []
    for ch in chapters:
        all_chunks.append(make_chapter_chunk(ch))
        all_chunks.extend(make_lesson_chunks(ch))
        all_chunks.extend(make_section_chunks(ch))

    # Normalize LaTeX / unicode
    for chunk in all_chunks:
        chunk["content"] = norm(chunk["content"])

    print(f"[chunker] Tổng chunks: {len(all_chunks)}")
    return all_chunks


def get_or_create_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
) -> None:
    """Tạo collection nếu chưa tồn tại."""
    existing = {c.name for c in client.get_collections().collections}
    if collection_name in existing:
        print(f"[qdrant] Collection '{collection_name}' đã tồn tại, dùng lại.")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"[qdrant] Đã tạo collection '{collection_name}' (dim={vector_size}).")


def chunks_to_points(
    chunks: list[dict],
    vectors: list[list[float]],
) -> list[PointStruct]:
    points = []
    for chunk, vector in zip(chunks, vectors):
        points.append(
            PointStruct(
                id      = str(uuid.uuid4()),
                vector  = vector,
                payload = {
                    "content" : chunk["content"],
                    **chunk["metadata"],
                },
            )
        )
    return points


def upload_in_batches(
    client: QdrantClient,
    collection_name: str,
    points: list[PointStruct],
    batch_size: int = BATCH_SIZE,
) -> None:
    total = len(points)
    for i in range(0, total, batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        print(f"[qdrant] Đã upload {min(i + batch_size, total)}/{total} points")


# ── Main ──────────────────────────────────────────────────────────────────────

def index(
    filepath: str,
    qdrant_url: str,
    qdrant_api_key: str,
    collection_name: str = COLLECTION_NAME,
) -> None:
    # 1. Chunking
    all_chunks = build_chunks(filepath)

    # 2. Embedding
    print(f"[embed] Đang load model '{EMBEDDING_MODEL}' ...")
    embed_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    texts   = [c["content"] for c in all_chunks]
    print(f"[embed] Đang embed {len(texts)} chunks ...")
    vectors: list[list[float]] = embed_model.embed_documents(texts)
    vector_size = len(vectors[0])
    print(f"[embed] Xong. Vector dim = {vector_size}")

    # 3. Qdrant client
    client = QdrantClient(
        url    = qdrant_url,
        api_key= qdrant_api_key,
    )

    # 4. Tạo collection
    get_or_create_collection(client, collection_name, vector_size)

    # 5. Build points & upload
    points = chunks_to_points(all_chunks, vectors)
    upload_in_batches(client, collection_name, points)

    print(f"\n✅ Hoàn tất! Đã index {len(points)} points vào '{collection_name}'.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # from config import env_config   # import env của dự án

    DOC_PATH = r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\src\modules\rag\documents\toan_10\documents\grade_10_chan_troi_sang_tao_toan_1.md"

    index(
        filepath       = DOC_PATH,
        qdrant_url     = env_config.qdrant_url,
        qdrant_api_key = env_config.qdrant_api_key,
        collection_name= "doc_toan_10_1",
    )
    print("ok")
