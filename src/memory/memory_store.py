import logging
import uuid
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import UserMemory

logger = logging.getLogger(__name__)

COLLECTION_NAME = "user_memories"
VECTOR_SIZE = 1  # dummy vector, không dùng similarity search


class MemoryStore:

    def __init__(self, url: str, api_key: str):
        self._client = QdrantClient(
            url=url,
            api_key=api_key,
            check_compatibility=False,
        )
        self._ensure_collection()

    def _ensure_collection(self):
        """Tạo collection nếu chưa có."""
        existing = [c.name for c in self._client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            self._client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"[MemoryStore] Created collection: {COLLECTION_NAME}")
        else:
            logger.info(f"[MemoryStore] Collection already exists: {COLLECTION_NAME}")

    def save(self, memory: dict):
        """
        Lưu hoặc cập nhật memory theo thread_id.
        Nếu đã có record với thread_id đó → upsert ghi đè.
        """
        thread_id = memory.get("thread_id")
        if not thread_id:
            logger.error("[MemoryStore] memory thiếu thread_id, bỏ qua")
            return

        # Dùng thread_id làm point ID (hash sang UUID)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, thread_id))

        point = PointStruct(
            id=point_id,
            vector=[0.0],   # dummy vector
            payload=memory,
        )

        self._client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point],
        )
        logger.info(f"[MemoryStore] Saved memory | thread_id={thread_id} | point_id={point_id}")

    def load(self, thread_id: str) -> Optional[dict]:
        """
        Load memory theo thread_id.
        Trả về dict nếu có, None nếu không có.
        """
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, thread_id))

        results = self._client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[point_id],
            with_payload=True,
        )

        if not results:
            logger.info(f"[MemoryStore] Không tìm thấy memory | thread_id={thread_id}")
            return None

        payload = results[0].payload
        logger.info(f"[MemoryStore] Loaded memory | thread_id={thread_id} | data={payload}")
        return payload

    def load_as_model(self, thread_id: str) -> Optional[UserMemory]:
        """Load memory và trả về UserMemory model."""
        payload = self.load(thread_id)
        if payload is None:
            return None
        try:
            return UserMemory(**payload)
        except Exception as e:
            logger.error(f"[MemoryStore] Parse UserMemory thất bại: {e}")
            return None

    def delete(self, thread_id: str):
        """Xóa memory theo thread_id."""
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, thread_id))
        self._client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[point_id],
        )
        logger.info(f"[MemoryStore] Deleted memory | thread_id={thread_id}")