import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import logging
from datetime import datetime
from typing import Optional
from langchain_core.messages import AnyMessage
from src.clients.llm import LLMClient

logger = logging.getLogger(__name__)

# ============================================================
# PROMPT - Quy tắc cứng: chỉ điền nếu user nói rõ ràng
# ============================================================

EXTRACT_PROMPT = """Bạn là hệ thống trích xuất thông tin có cấu trúc từ hội thoại về bệnh lúa.

NHIỆM VỤ:
Đọc đoạn hội thoại và điền vào các trường bên dưới.

QUY TẮC BẮT BUỘC:
- Chỉ điền nếu người dùng NÓI RÕ RÀNG trong hội thoại
- Không suy luận, không bịa đặt, không đoán mò
- Không chắc chắn → để null
- Chỉ trả về JSON, không giải thích thêm

CÁC TRƯỜNG CẦN ĐIỀN:
{{
    "location": <string | null>,           // vị trí ruộng, tỉnh/huyện nếu user đề cập
    "rice_stage": <string | null>,         // giai đoạn lúa: mạ / đẻ nhánh / làm đòng / trổ bông / chín
    "current_disease": <string | null>,    // bệnh đang xử lý hiện tại
    "disease_history": <list[str] | []>,   // tất cả bệnh đã đề cập trong hội thoại
    "last_topic": <string | null>,         // chủ đề cuối cùng đang hỏi
    "disease_progress": <string | null>    // tiến độ xử lý: "mới phát hiện" / "đang phun thuốc" / "đã xử lý"
                                           // chỉ điền nếu user nói rõ
}}

HỘI THOẠI:
{history}

Chỉ trả về JSON hợp lệ, không có text nào khác.
"""


class MemoryExtractor:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def extract(
        self,
        history: list[AnyMessage],
        user_id: str,
        thread_id: str,
        existing_memory: Optional[dict] = None
    ) -> dict:
        """
        Trích xuất memory từ history.
        Nếu có existing_memory thì merge — ưu tiên giá trị mới nếu không null.
        """

        if not history:
            logger.warning("[MemoryExtractor] history rỗng, bỏ qua extract")
            return existing_memory or {}

        # Format history thành text
        history_text = "\n".join(
            f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
            for m in history
        )

        prompt = EXTRACT_PROMPT.format(history=history_text)

        try:
            response = self.llm_client._llm.invoke(prompt)
            raw = response.content.strip()

            # Strip markdown code block nếu có
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            extracted: dict = json.loads(raw)

        except json.JSONDecodeError as e:
            logger.error(f"[MemoryExtractor] JSON parse error: {e}\nRaw: {raw}")
            extracted = {}
        except Exception as e:
            logger.error(f"[MemoryExtractor] LLM error: {e}")
            extracted = {}

        # Merge với existing_memory
        merged = self._merge(existing_memory or {}, extracted)

        # Thêm metadata
        merged["user_id"] = user_id
        merged["thread_id"] = thread_id
        merged["updated_at"] = datetime.now().isoformat()

        logger.info(f"[MemoryExtractor] Extracted: {merged}")
        return merged

    def _merge(self, old: dict, new: dict) -> dict:
        """
        Merge old memory với new extracted.
        - Giá trị mới không null → ghi đè
        - Giá trị mới null → giữ giá trị cũ
        - disease_history → union 2 list, không trùng lặp
        """
        merged = dict(old)

        for key, new_val in new.items():
            if key == "disease_history":
                # Union 2 list
                old_list = old.get("disease_history", []) or []
                new_list = new_val or []
                merged["disease_history"] = list(dict.fromkeys(old_list + new_list))

            elif new_val is not None and new_val != "" and new_val != []:
                # Ghi đè nếu giá trị mới có nghĩa
                merged[key] = new_val

            else:
                # Giữ giá trị cũ nếu mới là null
                merged[key] = old.get(key)

        return merged