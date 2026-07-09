import sys
import os
import json
from typing import Optional
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State, SkeletonPhase

COLLECT_INFO_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\COLLECT_INFO.txt"
CREATE_SKELETON_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\CREATE_SKELETON.txt"


# ── SCHEMAS ───────────────────────────────────────────────────────────

class PlanContext(BaseModel):
    disease:             Optional[str] = Field(default=None, description="Mục tiêu chính: tên bệnh hoặc công việc. Ví dụ: đạo ôn, khô vằn, cải tạo đất.")
    location:            Optional[str] = Field(default=None, description="Địa điểm ruộng. Ví dụ: Quảng Nam, Cần Thơ.")
    duration_days:       Optional[int] = Field(default=None, description="Số ngày kế hoạch. Ví dụ: 7, 14, 21.")
    disease_scale:       Optional[str] = Field(default=None, description="Phạm vi bị ảnh hưởng. Ví dụ: vài khóm, cả ruộng.")
    disease_duration:    Optional[str] = Field(default=None, description="Thời gian xuất hiện. Ví dụ: hôm nay, 3 ngày.")
    disease_severity:    Optional[str] = Field(default=None, description="Mức độ. Ví dụ: nhẹ, trung bình, nặng.")
    rice_stage:          Optional[str] = Field(default=None, description="Giai đoạn lúa. Ví dụ: đẻ nhánh, làm đòng, trổ bông.")
    rice_variety:        Optional[str] = Field(default=None, description="Giống lúa. Ví dụ: OM5451, ST25.")
    current_medicine:    Optional[str] = Field(default=None, description="Thuốc đang dùng. Ví dụ: Tricyclazole, chưa xử lý.")
    weather_description: Optional[str] = Field(default=None, description="Thời tiết theo mô tả người dùng. Ví dụ: mưa nhiều, nắng nóng.")


class SkeletonOutput(BaseModel):
    skeleton: list[SkeletonPhase]


# ── HÀM 1: collect_info ──────────────────────────────────────────────

def collect_info(llm_client, state: State, user_message: str, current_context: dict = {}) -> dict:
    """
    Đọc COLLECT_INFO.txt, inject history + user_memory + context hiện tại.
    Dùng LLM trích xuất thông tin từ user_message → return PlanContext dict.
    """
    with open(COLLECT_INFO_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    history = list(state.get("history", []))[-6:]
    history_text = "\n".join(
        f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
        for m in history
    ) or "Chưa có lịch sử."

    user_memory = state.get("user_memory")
    user_memory_text = "Chưa có thông tin."
    if user_memory:
        data = user_memory if isinstance(user_memory, dict) else user_memory.model_dump()
        user_memory_text = "\n".join(
            f"- {k}: {v}" for k, v in data.items()
            if v and k not in ["user_id", "thread_id", "updated_at"]
        ) or "Chưa có thông tin."

    system_prompt = (
        template
        .replace("{history_text}", history_text)
        .replace("{user_memory}", user_memory_text)
    ) 
    print("=" * 20)
    print(f"system_prompt : {system_prompt}")


    # print(f"[collect_info] current_context:\n{json.dumps(current_context, ensure_ascii=False, indent=2)}")
    print("=" * 20)

    llm = llm_client._llm.with_structured_output(PlanContext)
    result: PlanContext = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ])


    print(f"result :\n{result}")
    return result


# ── HÀM 2: create_skeleton ───────────────────────────────────────────

def create_skeleton(llm_client, context: dict) -> list:
    """
    Đọc CREATE_SKELETON.txt, inject context.
    Dùng LLM sinh skeleton → return list[SkeletonPhase] dict.
    """
    with open(CREATE_SKELETON_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    system_prompt = template.replace(
        "{plan_context}", json.dumps(context, ensure_ascii=False, indent=2)
    )

    print("=" * 20)
    print(f"system_prompt create_skeleton :\n{system_prompt}")
    print("=" * 20)

    llm = llm_client._llm.with_structured_output(SkeletonOutput)
    result: SkeletonOutput = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": "Sinh skeleton kế hoạch dựa vào context trên."},
    ])

     
    print(f"result skeleton:\n{result}")
    return result



# SUMMARY_CONVER_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\SUMMARY_CONVER.txt"

# def make_summary_conver_tool(llm_client):

#     with open(SUMMARY_CONVER_PROMPT_PATH, "r", encoding="utf-8") as f:
#         template = f.read()

#     def summary_conver(query: str, response_collect: str) -> str:
#         """
#         Tóm tắt 1 cặp hội thoại (input + response) thành chuỗi ngắn gọn.

#         Args:
#             input_text: Tin nhắn người dùng.
#             response_text: Phản hồi của bot.

#         Returns:
#             str: Đoạn tóm tắt.
#         """
#         conversation = f"Người dùng: {query}\nBot: {response_collect}"
#         prompt = template.replace("{conversation}", conversation)

#         response = llm_client._llm.invoke([
#             {"role": "system", "content": prompt},
#             {"role": "user", "content": "Tóm tắt hội thoại trên."},
#         ])

#         return response.content.strip()

#     return StructuredTool.from_function(
#         func=summary_conver,
#         name="summary_conver",
#         description="Tóm tắt 1 cặp hội thoại người dùng - bot thành đoạn văn ngắn gọn.",
#     )