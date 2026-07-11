import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

# from langchain.schema import AIMessage
 
from langgraph.graph import END
from src.state import State , QueryExtract
from src.clients.llm import LLMClient
from langchain_core.messages import HumanMessage , AIMessage, SystemMessage



ROUTER_PROMPT = """Bạn là bộ định tuyến cho hệ thống chatbot hỏi đáp về bệnh trên lá lúa.

Nhiệm vụ: Đọc câu hỏi của người dùng và phân loại vào đúng route.

Các route:
- route: 1 → Câu hỏi liên quan đến bệnh trên lá lúa (triệu chứng, nguyên nhân, cách phòng trị, nhận diện bệnh, v.v.)
- route: 2 → Yêu cầu lập kế hoạch, tạo lịch trình phòng trị / cải tạo / khắc phục bệnh lúa theo ngày (lập kế hoạch, tạo plan, kế hoạch phòng ngừa, lịch phun thuốc, v.v.)
- route: 0 → Câu hỏi không liên quan đến bệnh lúa (chào hỏi, chủ đề khác, ngoài phạm vi)

Quy tắc phân biệt route 1 và route 2:
- route 1: hỏi thông tin, kiến thức về bệnh ("bệnh đạo ôn là gì", "triệu chứng khô vằn", "dùng thuốc gì")
- route 2: yêu cầu tạo kế hoạch hành động theo lịch trình ("lập kế hoạch phòng đạo ôn", "tạo lịch phun thuốc 14 ngày", "kế hoạch xử lý bệnh khô vằn")

Quy tắc trả lời:
- Chỉ trả về đúng 2 dòng, không giải thích thêm
- Dòng 1: route: <số>
- Dòng 2: reason: <lý do ngắn gọn bằng tiếng Việt>

Lưu ý : nếu đang bàn về kế hoạch thì route luôn là 2 khi người dùng nói chủ đề khác thì hỏi họ muốn thoát khỏi tạo kế hoạch không nếu có thì dùng router như nhiệm vụ

Ví dụ 1:
Câu hỏi: "Lá lúa bị vàng từ chóp lá xuống là bệnh gì?"
route: 1
reason: Người dùng hỏi về triệu chứng bệnh trên lá lúa.

Ví dụ 2:
Câu hỏi: "Hôm nay thời tiết thế nào?"
route: 0
reason: Câu hỏi không liên quan đến bệnh lúa.

Ví dụ 3:
Câu hỏi: "Lập kế hoạch phòng bệnh đạo ôn 14 ngày cho ruộng của tôi"
route: 2
reason: Người dùng yêu cầu tạo kế hoạch phòng bệnh theo lịch trình.

Ví dụ 4:
Câu hỏi: "Tạo lịch phun thuốc xử lý bệnh khô vằn"
route: 2
reason: Người dùng yêu cầu lập lịch hành động xử lý bệnh.
"""

DISEASE_MAPPING = {
    "DỮ LIỆU BỆNH HỌC: BỆNH ĐẠO ÔN LÁ": "LEAF BLAST",
    "BỆNH ĐỐM LÁ HẸP / GẠCH NÂU": "NARROW BROWN LEAF SPOT",
    "BỆNH ĐỐM NÂU": "BROWN SPOT",
    "BỆNH KHÔ VẰN": "SHEATH BLIGHT",
    "BỆNH BẠC LÁ": "BACTERIAL LEAF BLIGHT - BLB",
    "BỆNH BỎNG LÁ": "RICE LEAF YELLOWING",
    "LÁ LÚA KHỎE MẠNH": "HEALTHY RICE LEAF"
}

DISEASE_MAPPING_TEXT = "\n".join(f"- {vn}: {en}" for vn, en in DISEASE_MAPPING.items())

QUERY_TRANSFORM_PROMPT = f"""Bạn là chuyên gia phân tích câu hỏi về bệnh trên lá lúa.

Nhiệm vụ:
1. Dựa vào lịch sử hội thoại, làm rõ câu hỏi hiện tại (giải quyết đại từ "nó", "như trên", "bệnh đó"...)
2. Trích xuất thông tin có cấu trúc từ câu hỏi đã làm rõ

Danh sách bệnh được hỗ trợ (tên tiếng Việt: tên khoa học):
{DISEASE_MAPPING_TEXT}

Quy tắc:
- Chỉ điền disease/scientific_name nếu câu hỏi đề cập rõ ràng hoặc suy luận chắc chắn từ context
- Nếu không xác định được → để trống (không bịa đặt)
- disease và scientific_name phải là một cặp và lấy đúng từ danh sách mapping trên , có thể 1 hoặc nhiều giá trị và trả lời cách nhau dấu phẩy 
- ví dụ: disease: BỆNH ĐẠO ÔN LÁ, BỆNH KHÔ VẰN   ← nhiều bệnh cách nhau bằng dấu phẩy
- keywords: tối đa 5 từ khóa quan trọng liên quan đến nội dung câu hỏi
- Trả về đúng format sau, không giải thích thêm

Format trả về:
query_clear: <câu hỏi đã làm rõ>
disease: <tên tiếng Việt hoặc để trống>
scientific_name: <tên khoa học hoặc để trống>
topic: <chủ đề chính của câu hỏi>
keywords: <từ khóa 1>, <từ khóa 2>, ...

Ví dụ 1:
Lịch sử:
Người dùng: bệnh đạo ôn do đâu mà ra?
Bot: Do nấm Pyricularia oryzae gây ra.

Câu hỏi hiện tại: "có nguy hiểm không"

query_clear: bệnh đạo ôn có nguy hiểm không
disease: DỮ LIỆU BỆNH HỌC: BỆNH ĐẠO ÔN LÁ
scientific_name: LEAF BLAST
topic: mức độ nguy hiểm
keywords: nguy hiểm, lây lan, thiệt hại, nấm, Pyricularia

Ví dụ 2:
Lịch sử: 
Người dùng: bệnh bạc lá nên dùng thuốc gì?
Bot: các loại thuốc như Kasumin, Antracol để điều trị bệnh bạc lá.    

Câu hỏi hiện tại: "nó khác bệnh khô vằn sao?"

query_clear: bệnh bạc lá khác bệnh khô vằn sao?
disease: BỆNH BẠC LÁ , BỆNH KHÔ VẰN
scientific_name: BACTERIAL LEAF BLIGHT - BLB,SHEATH BLIGHT
topic: sự khác nhau 2 bệnh
keywords: khác biệt, so sánh , khô vằn , bạc lá
"""

class RouterAgent:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def __call__(self, state: State) -> dict:
        print("======================================= Router_Agent =======================================")

        def query_transform(state: State) -> dict:
            messages = state.get("messages", [])
            user_message = [msg.content for msg in messages if msg.type == "human"][-1]

            history_text = "\n".join(
                f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
                for m in messages[:-1][-6:]
            )

            prompt = QUERY_TRANSFORM_PROMPT
            if history_text:
                prompt += f"\nLịch sử:\n{history_text}\n"
            prompt += f"\nCâu hỏi hiện tại: \"{user_message}\""

            response = self.llm_client._llm.invoke(prompt)
            raw = response.content.strip()

            result = {"query_clear": user_message, "disease": None, "scientific_name": None, "topic": None, "keywords": []}
            for line in raw.split("\n"):
                line = line.strip()
                if line.startswith("query_clear:"):
                    result["query_clear"] = line.split("query_clear:")[1].strip()
                elif line.startswith("disease:"):
                    val = line.split("disease:")[1].strip()
                    result["disease"] = [d.strip() for d in val.split(",")] if val else None
                elif line.startswith("scientific_name:"):
                    val = line.split("scientific_name:")[1].strip()
                    result["scientific_name"] = val if val else None
                elif line.startswith("topic:"):
                    result["topic"] = line.split("topic:")[1].strip()
                elif line.startswith("keywords:"):
                    kw = line.split("keywords:")[1].strip()
                    result["keywords"] = [k.strip() for k in kw.split(",") if k.strip()]

            valid_scientific = set(DISEASE_MAPPING.values())
            if result["scientific_name"] not in valid_scientific:
                result["scientific_name"] = None

            query_extract = QueryExtract(**result)
            return {"query_extract": query_extract}

        # Bước 1: làm rõ query + trích xuất
        transform_result = query_transform(state)
        state = {**state, **transform_result}

        query_clear = state["query_extract"].query_clear

        messages = state.get("messages", [])
        history_text = "\n".join(
            f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
            for m in messages[:-1][-6:]
        )

        prompt = ROUTER_PROMPT
        if history_text:
            prompt += f"\nLịch sử hội thoại:\n{history_text}\n"
        prompt += f"\nCâu hỏi hiện tại: \"{query_clear}\""

        response = self.llm_client._llm.invoke(prompt)
        llm_output = response.content.strip()

        print(f"[Router] LLM output:\n{llm_output}")

        route = None
        reason = ""
        for line in llm_output.split("\n"):
            line = line.strip()
            if line.startswith("route:"):
                try:
                    route = int(line.split("route:")[1].strip())
                except ValueError:
                    route = None
            elif line.startswith("reason:"):
                reason = line.split("reason:")[1].strip()

        print(f"[Router] route={route}, reason={reason}")

        if route == 1:
            return {"route": 2, "state_router": True, "query_extract": transform_result}
        elif route == 2:
            return {"route": 2, "state_router": True, "query_extract": transform_result}
        else:
            return {"route": 0, "state_router": False, "query_extract": transform_result}