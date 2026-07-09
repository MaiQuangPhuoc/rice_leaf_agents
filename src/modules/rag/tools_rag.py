# tools_rag.py
from typing import List
from uuid import uuid4
    
from typing import List, Tuple
from typing import List, Optional
from qdrant_client.http.models import Filter
from datetime import datetime
import time
class RAGTools:
    def __init__(self, vector_store, max_nodes: int = 5):
        self.vector_store = vector_store
        self.max_nodes = max_nodes
        self.client = vector_store._client
        self.collection_name = vector_store.collection_name

    # ===================================================================
    # 1. Hàm tạo timestamp an toàn (không bao giờ bị xóa nhầm point đầu)
    # ===================================================================
    def _get_timestamp(self) -> int:
        """Trả về timestamp dạng int: YYMMDDHHMMSS → đảm bảo tăng dần, không âm"""
        return int(datetime.now().strftime("%y%m%d%H%M%S"))

    def _get_time_str(self) -> str:
        """Dạng đẹp để hiển thị: 14:30 08/12"""
        return datetime.now().strftime("%H:%M %d/%m")

    # ===================================================================
    # 2. Xóa sạch hoàn toàn bộ nhớ (reset như mới)
    # ===================================================================
    def delete_all_nodes(self):
        """
        Xóa sạch toàn bộ các point (tin nhắn) trong collection
        → Chỉ xóa dữ liệu, giữ nguyên collection (không cần tạo lại)
        """
        print(f"Đang xóa sạch toàn bộ tin nhắn trong collection '{self.collection_name}'...")

        # 1. Lấy hết tất cả points (giống hệt cách trong _enforce_limit_before_add)
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        
        all_points = points.copy()
        while len(points) == 1000:  # còn dữ liệu → tiếp tục scroll
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                offset=points[-1].id,
                with_payload=True,
                with_vectors=False
            )
            all_points.extend(points)

        total = len(all_points)
        if total == 0:
            print("Collection đã trống từ trước!")
            return

        # 2. Lấy danh sách ID của tất cả points
        ids_to_delete = [p.id for p in all_points]

        # 3. Xóa một lần duy nhất → cực nhanh
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids_to_delete
        )

        print(f"Đã xóa sạch {total} tin nhắn thành công! Collection '{self.collection_name}' giờ trống.")

    # ===================================================================
    # 3. Giữ lại đúng (max_nodes - 1) point mới nhất trước khi thêm
    # ===================================================================
    def _enforce_limit_before_add(self):
        """
        Xóa các tin nhắn cũ nhất để còn chỗ cho tin nhắn mới
        → Chỉ còn (max_nodes - 1) tin nhắn mới nhất
        """
        # 1. Lấy hết points
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        all_points = points.copy()
        while len(points) == 1000:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                offset=points[-1].id,
                with_payload=True,
                with_vectors=False
            )
            all_points.extend(points)

        total = len(all_points)
        if total < self.max_nodes:
            return

        # 2. Tạo list chỉ chứa (point, timestamp) để dễ sort
        points_with_time = []
        for p in all_points:
            ts = p.payload.get("metadata", {}).get("timestamp", 0)  # ← đúng chỗ
            points_with_time.append((ts, p))

        # 3. Sắp xếp tăng dần theo timestamp → cũ nhất ở đầu
        points_with_time.sort(key=lambda x: x[0])  # sort theo ts

        # for ts, p in points_with_time:
        #     print(f"Timestamp: {ts} --- Content: {p.payload.get('page_content', '')}")         

        # 4. Tính số cần xóa
        keep_count = self.max_nodes - 1
        num_to_delete = total - keep_count
        if num_to_delete <= 0:
            return

        # 5. Lấy các point cũ nhất để xóa
        points_to_delete = points_with_time[:num_to_delete]
        ids_to_delete = [p.id for _, p in points_to_delete]

        # 6. Xóa thật
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids_to_delete
        )

        print(f"Đã xóa {num_to_delete} tin nhắn cũ nhất → còn {keep_count} tin nhắn mới nhất")

    # ===================================================================
    # 4. Thêm node mới (chính)
    # ===================================================================
    def add_node(self, text: str, metadata: Optional[dict] = None) -> str:
        """
        Thêm một tin nhắn vào bộ nhớ, tự động giữ đúng max_nodes tin mới nhất
        """

        print("===== Thêm node mới =====")
        if metadata is None:
            metadata = {}

        # Tự động thêm timestamp an toàn + thời gian đẹp
        metadata["timestamp"] = self._get_timestamp()
        metadata["time_str"] = self._get_time_str()

        # Đảm bảo còn chỗ trước khi thêm
        self._enforce_limit_before_add()

        # Thêm mới
        doc_id = str(uuid4())
        self.vector_store.add_texts(
            texts=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

        # Log đẹp
        short_text = text.strip().replace("\n", " ")
        if len(short_text) > 80:
            short_text = short_text[:77] + "..."

        print(f"Thêm mới [{metadata['time_str']}] → \"{short_text}\"")

        return doc_id


    def retrieve_top_k(self, query: str, k: int = 3) -> List[Tuple[str, float, dict]]:
        hits = self.vector_store.similarity_search_with_score(
            query=query,
            k=k * 3 
        )

        results = []
        for doc, score in hits:
            text = doc.page_content
            metadata = doc.metadata
            # print("RAG Tools - Retrieved:", text, "---- (Score:", score, ")")

            results.append((text, float(score), metadata))

        results.sort(key=lambda x: x[1], reverse=True)
        
       
        top_k_results = results[:k]
        # for text, score in enumerate(top_k_results):
            # print(f"RAG Tools - Top {text} ---- (Score: {score})")   



        return top_k_results
